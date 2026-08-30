import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.api.deps import get_db, get_redis, get_current_user
from app.models.user import User
from app.models.order import Order
from app.services.redis_service import RedisService
from app.services.idempotency_service import IdempotencyService
from app.services.payment_service import PaymentGatewaySimulator
from app.services.rate_limiter import DistributedRateLimiter, RateLimitScope
from app.core.metrics import payments_total

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

class PaymentChargeRequest(BaseModel):
    order_id: int
    simulate_failure: bool = False
    simulate_timeout: bool = False

@router.post(
    "/charge",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(DistributedRateLimiter.rate_limit(RateLimitScope.PAYMENTS_CHARGE, max_requests=5, window_seconds=60))]
)
async def charge_order(
    request: Request,
    response: Response,
    payload: PaymentChargeRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    Production-Grade Payment Processing Endpoint with Observability Metrics.
    """
    user_id = current_user.id

    # 1. Validate Idempotency-Key & Compute Fingerprint
    valid_key = IdempotencyService.validate_key(idempotency_key)
    req_hash = IdempotencyService.compute_fingerprint(
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        payload=payload.model_dump()
    )

    is_completed, cached_response = await IdempotencyService.start_or_replay(
        db=db,
        redis=redis,
        idempotency_key=valid_key,
        user_id=user_id,
        req_hash=req_hash
    )

    if is_completed and cached_response is not None:
        response.headers["X-Idempotent-Replay"] = "true"
        return cached_response

    # 2. Authorization & Order Existence Check
    order_res = await db.execute(select(Order).where(Order.id == payload.order_id))
    order = order_res.scalar_one_or_none()

    if not order:
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {payload.order_id} not found."
        )

    if order.user_id != user_id:
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to settle payments for this order."
        )

    if order.status == "PAID":
        response_data = {
            "status": "PAID",
            "order_id": order.id,
            "total_amount": float(order.total_amount),
            "message": "Order is already settled."
        }
        await IdempotencyService.mark_completed(
            db=db, redis=redis, idempotency_key=valid_key, user_id=user_id,
            status_code=200, response_body=response_data
        )
        await db.commit()
        return response_data

    if order.status == "PROCESSING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment charge is currently in progress for this order. Please wait."
        )

    if order.status == "CANCELLED":
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot settle payment for a cancelled order."
        )

    # 3. Atomic State Transition: PENDING/FAILED -> PROCESSING
    stmt = (
        update(Order)
        .where(
            Order.id == payload.order_id,
            Order.user_id == user_id,
            Order.status.in_(["PENDING", "FAILED"])
        )
        .values(status="PROCESSING")
        .execution_options(synchronize_session=False)
        .returning(Order.id, Order.total_amount, Order.status)
    )
    transition_res = await db.execute(stmt)
    transition_row = transition_res.first()

    if not transition_row:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order state changed concurrently. Unable to claim payment processing lock."
        )

    await db.commit()

    # 4. External Payment Gateway Execution
    charge_amount = float(transition_row.total_amount)
    try:
        charge_result = await PaymentGatewaySimulator.process_charge(
            amount=charge_amount,
            order_id=payload.order_id,
            idempotency_key=valid_key,
            simulate_failure=payload.simulate_failure,
            simulate_timeout=payload.simulate_timeout
        )
    except TimeoutError:
        payments_total.labels(status="TIMEOUT").inc()
        logger.warning(f"Payment gateway timeout for order {payload.order_id}")
        await db.execute(
            update(Order).where(Order.id == payload.order_id).values(status="FAILED")
        )
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Payment gateway communication timed out. Order status marked as FAILED. You may retry."
        )
    except Exception as e:
        payments_total.labels(status="ERROR").inc()
        logger.error(f"Unexpected payment error for order {payload.order_id}: {e}", exc_info=True)
        await db.execute(
            update(Order).where(Order.id == payload.order_id).values(status="FAILED")
        )
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with payment gateway. Please retry."
        )

    # 5. Finalize State: PROCESSING -> PAID or FAILED
    if charge_result.get("success"):
        payments_total.labels(status="PAID").inc()
        await db.execute(
            update(Order).where(Order.id == payload.order_id).values(status="PAID")
        )
        response_data = {
            "status": "PAID",
            "order_id": payload.order_id,
            "transaction_id": charge_result["transaction_id"],
            "total_amount": charge_amount
        }
        await IdempotencyService.mark_completed(
            db=db,
            redis=redis,
            idempotency_key=valid_key,
            user_id=user_id,
            status_code=200,
            response_body=response_data
        )
        await db.commit()
        return response_data
    else:
        payments_total.labels(status="FAILED").inc()
        await db.execute(
            update(Order).where(Order.id == payload.order_id).values(status="FAILED")
        )
        await IdempotencyService.mark_failed(db, redis, valid_key, user_id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment declined: {charge_result.get('error_message', 'Card declined')}"
        )

@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Order).where(Order.id == order_id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found."
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this order."
        )

    return {
        "order_id": order.id,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }