import logging
from decimal import Decimal
from collections import defaultdict
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_redis, get_current_user
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.redis_service import RedisService
from app.services.idempotency_service import IdempotencyService
from app.services.rate_limiter import DistributedRateLimiter, RateLimitScope
from app.services.websocket_service import manager
from app.core.metrics import (
    orders_created_total,
    flash_sale_requests_total,
    inventory_reservations_total
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")

class CreateOrderRequest(BaseModel):
    user_id: Optional[int] = None
    items: List[OrderItemInput]

@router.get("/", status_code=status.HTTP_200_OK)
async def list_user_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all historical orders for the authenticated user."""
    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    res = await db.execute(stmt)
    orders = res.scalars().all()

    output = []
    for ord_obj in orders:
        items_res = await db.execute(select(OrderItem).where(OrderItem.order_id == ord_obj.id))
        items = items_res.scalars().all()
        output.append({
            "id": ord_obj.id,
            "user_id": ord_obj.user_id,
            "total_amount": float(ord_obj.total_amount),
            "status": ord_obj.status,
            "created_at": ord_obj.created_at,
            "updated_at": ord_obj.updated_at,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price)
                }
                for item in items
            ]
        })
    return output

@router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves single order details with ownership verification."""
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

    items_res = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = items_res.scalars().all()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": float(order.total_amount),
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price)
            }
            for item in items
        ]
    }

@router.post(
    "/flash-checkout",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(DistributedRateLimiter.rate_limit(RateLimitScope.FLASH_SALE, max_requests=5, window_seconds=10))]
)
async def flash_checkout(
    request: Request,
    response: Response,
    payload: CreateOrderRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    Optimized Flash Sale Hot-Path with End-to-End Metrics & Observability.
    """
    user_id = current_user.id

    # 1. Validate Key & Compute Deterministic Fingerprint
    valid_key = IdempotencyService.validate_key(idempotency_key)
    payload_dict = payload.model_dump()
    req_hash = IdempotencyService.compute_fingerprint(
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        payload=payload_dict
    )

    # 2. Atomic Idempotency State Claim / Replay Check
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

    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item."
        )

    # 3. Normalize and Sort Items (Deadlock Prevention)
    aggregated_items: dict[int, int] = defaultdict(int)
    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quantity {item.quantity} for product ID {item.product_id}."
            )
        aggregated_items[item.product_id] += item.quantity

    sorted_items = sorted(aggregated_items.items(), key=lambda x: x[0])

    # 4. Redis Admission Control & Reservation (Zero DB Load on Sold Out)
    redis_reserved = False
    redis_available = await redis.is_available()

    if redis_available:
        reserve_status, err_idx = await redis.reserve_multi(sorted_items)

        # Handle cold-start cache misses safely using SETNX
        if reserve_status == -1:
            for pid, _ in sorted_items:
                res = await db.execute(select(Product.stock).where(Product.id == pid))
                stock_val = res.scalar_one_or_none()
                if stock_val is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product ID {pid} not found."
                    )
                await redis.safe_initialize_stock(pid, stock_val)

            reserve_status, err_idx = await redis.reserve_multi(sorted_items)

        if reserve_status == 0:
            inventory_reservations_total.labels(result="OUT_OF_STOCK").inc()
            flash_sale_requests_total.labels(result="REJECTED_SOLD_OUT").inc()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="One or more items are out of stock in flash cache."
            )
        elif reserve_status == 1:
            redis_reserved = True
            inventory_reservations_total.labels(result="SUCCESS").inc()
            flash_sale_requests_total.labels(result="ADMITTED").inc()

    # 5. PostgreSQL Authoritative Atomic Decrement & Persistence
    try:
        total_amount = Decimal("0.00")
        order_items_data = []
        updated_stocks = {}

        for product_id, qty in sorted_items:
            stmt = (
                update(Product)
                .where(Product.id == product_id, Product.stock >= qty)
                .values(stock=Product.stock - qty)
                .execution_options(synchronize_session=False)
                .returning(Product.id, Product.price, Product.stock, Product.title)
            )
            res = await db.execute(stmt)
            row = res.first()

            if not row:
                inventory_reservations_total.labels(result="DB_OUT_OF_STOCK").inc()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient inventory in database for product ID {product_id}."
                )

            unit_price = Decimal(str(row.price))
            item_total = unit_price * qty
            total_amount += item_total
            updated_stocks[product_id] = row.stock

            order_items_data.append({
                "product_id": product_id,
                "quantity": qty,
                "unit_price": unit_price
            })

        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status="PAID"
        )
        db.add(new_order)
        await db.flush()

        for itm in order_items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=itm["product_id"],
                quantity=itm["quantity"],
                unit_price=itm["unit_price"]
            )
            db.add(order_item)

        response_data = {
            "order_id": new_order.id,
            "status": "PAID",
            "total_amount": float(total_amount),
            "items": [
                {
                    "product_id": itm["product_id"],
                    "quantity": itm["quantity"],
                    "unit_price": float(itm["unit_price"])
                }
                for itm in order_items_data
            ]
        }

        await IdempotencyService.mark_completed(
            db=db,
            redis=redis,
            idempotency_key=valid_key,
            user_id=user_id,
            status_code=201,
            response_body=response_data
        )

        await db.commit()
        orders_created_total.labels(status="PAID").inc()

    except Exception as e:
        await db.rollback()
        await IdempotencyService.mark_failed(
            db=db,
            redis=redis,
            idempotency_key=valid_key,
            user_id=user_id
        )
        if redis_reserved:
            await redis.compensate_batch(sorted_items)
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Checkout transaction failed unexpectedly: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Checkout transaction failed. No funds or inventory were charged."
        )

    # 6. Post-Commit Asynchronous Broadcasts
    for pid, new_stock in updated_stocks.items():
        try:
            await manager.broadcast_stock_update(pid, new_stock)
        except Exception:
            pass

    return response_data