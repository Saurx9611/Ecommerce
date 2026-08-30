import hashlib
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Tuple, Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.idempotency import IdempotencyRecord
from app.services.redis_service import RedisService
from app.core.metrics import idempotency_operations_total

logger = logging.getLogger(__name__)

IDEMPOTENCY_KEY_REGEX = re.compile(r"^[A-Za-z0-9_\-\:]{1,128}$")
LOCK_TIMEOUT_SECONDS = 30

class IdempotencyService:
    @staticmethod
    def validate_key(idempotency_key: Optional[str]) -> str:
        """Validates that the idempotency key is present, non-empty, and well-formatted."""
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key header is required for this operation and cannot be empty."
            )
        key = idempotency_key.strip()
        if len(key) > 128 or not IDEMPOTENCY_KEY_REGEX.match(key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key must be 1-128 characters containing only alphanumeric, '-', '_', or ':'."
            )
        return key

    @staticmethod
    def compute_fingerprint(method: str, path: str, user_id: int, payload: Dict[str, Any]) -> str:
        """Generates a deterministic SHA-256 fingerprint."""
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        raw_str = f"{method.upper()}:{path}:{user_id}:{canonical_json}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    @staticmethod
    async def start_or_replay(
        db: AsyncSession,
        redis: RedisService,
        idempotency_key: str,
        user_id: int,
        req_hash: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        now = datetime.now(timezone.utc)
        locked_until = now + timedelta(seconds=LOCK_TIMEOUT_SECONDS)

        # 1. Fast admission check in Redis
        redis_key = f"idempotency:{user_id}:{idempotency_key}"
        if redis.client:
            try:
                acquired = await redis.client.set(redis_key, req_hash, nx=True, ex=LOCK_TIMEOUT_SECONDS)
                if not acquired:
                    stored_hash = await redis.client.get(redis_key)
                    if stored_hash and stored_hash != req_hash:
                        idempotency_operations_total.labels(action="CONFLICT").inc()
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Idempotency key reused with mismatched request payload."
                        )
            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                logger.warning(f"Redis idempotency lock error: {e}")

        # 2. Database Authority check & Atomic Claim
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == idempotency_key,
            IdempotencyRecord.user_id == user_id
        ).with_for_update()
        
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if record:
            if record.request_hash != req_hash:
                idempotency_operations_total.labels(action="CONFLICT").inc()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with mismatched request payload."
                )

            if record.status == "COMPLETED":
                idempotency_operations_total.labels(action="REPLAYED").inc()
                return True, record.response_body

            if record.status == "IN_PROGRESS":
                locked_val = record.locked_until
                if locked_val and locked_val.tzinfo is None:
                    locked_val = locked_val.replace(tzinfo=timezone.utc)

                if locked_val and locked_val > now:
                    idempotency_operations_total.labels(action="IN_PROGRESS_BLOCKED").inc()
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A concurrent request with this Idempotency-Key is currently in progress. Please wait."
                    )
                record.locked_until = locked_until
                record.updated_at = now
                await db.flush()
                idempotency_operations_total.labels(action="LOCK_ACQUIRED").inc()
                return False, None

            if record.status == "FAILED":
                record.status = "IN_PROGRESS"
                record.locked_until = locked_until
                record.updated_at = now
                await db.flush()
                idempotency_operations_total.labels(action="RETRY_ACQUIRED").inc()
                return False, None

        # 3. Create new record in IN_PROGRESS state
        new_record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            user_id=user_id,
            request_hash=req_hash,
            status="IN_PROGRESS",
            locked_until=locked_until
        )
        db.add(new_record)
        try:
            await db.flush()
            idempotency_operations_total.labels(action="NEW").inc()
        except IntegrityError:
            await db.rollback()
            idempotency_operations_total.labels(action="CONFLICT").inc()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent request already claimed this Idempotency-Key."
            )

        return False, None

    @staticmethod
    async def mark_completed(
        db: AsyncSession,
        redis: RedisService,
        idempotency_key: str,
        user_id: int,
        status_code: int,
        response_body: Dict[str, Any]
    ):
        now = datetime.now(timezone.utc)
        stmt = (
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.idempotency_key == idempotency_key,
                IdempotencyRecord.user_id == user_id
            )
            .values(
                status="COMPLETED",
                status_code=status_code,
                response_body=response_body,
                locked_until=None,
                updated_at=now
            )
        )
        await db.execute(stmt)

        redis_key = f"idempotency:{user_id}:{idempotency_key}"
        if redis.client:
            try:
                await redis.client.set(f"{redis_key}:resp", json.dumps(response_body), ex=86400)
            except Exception as e:
                logger.warning(f"Failed to cache completed idempotency response in Redis: {e}")

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        redis: RedisService,
        idempotency_key: str,
        user_id: int
    ):
        now = datetime.now(timezone.utc)
        stmt = (
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.idempotency_key == idempotency_key,
                IdempotencyRecord.user_id == user_id
            )
            .values(
                status="FAILED",
                locked_until=None,
                updated_at=now
            )
        )
        await db.execute(stmt)

        redis_key = f"idempotency:{user_id}:{idempotency_key}"
        if redis.client:
            try:
                await redis.client.delete(redis_key)
            except Exception:
                pass
