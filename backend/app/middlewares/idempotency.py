from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.idempotency_service import IdempotencyService
from app.services.redis_service import RedisService

async def verify_idempotency_request(
    request: Request,
    idempotency_key: Optional[str],
    user_id: int,
    payload: Dict[str, Any],
    db: AsyncSession,
    redis: RedisService
):
    """
    Middleware verification helper validating header, fingerprint, and replay status.
    """
    valid_key = IdempotencyService.validate_key(idempotency_key)
    req_hash = IdempotencyService.compute_fingerprint(
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        payload=payload
    )

    is_completed, cached_response = await IdempotencyService.start_or_replay(
        db=db,
        redis=redis,
        idempotency_key=valid_key,
        user_id=user_id,
        req_hash=req_hash
    )

    return valid_key, req_hash, is_completed, cached_response