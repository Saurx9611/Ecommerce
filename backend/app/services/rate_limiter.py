import logging
from typing import Callable
from fastapi import Request, HTTPException, status, Depends
from app.services.redis_service import RedisService
from app.api.deps import get_redis
from app.core.metrics import rate_limit_blocks_total

logger = logging.getLogger(__name__)

class RateLimitScope:
    AUTH_LOGIN = "auth:login"
    AUTH_REGISTER = "auth:register"
    PRODUCT_CREATE = "products:create"
    ORDERS_CHECKOUT = "orders:checkout"
    PAYMENTS_CHARGE = "payments:charge"
    FLASH_SALE = "orders:flash_sale"

class DistributedRateLimiter:
    """
    Production-grade distributed rate limiter backed by Redis sliding window Lua evaluation.
    Protects sensitive endpoint classes across multiple load-balanced backend instances.
    """
    @staticmethod
    def rate_limit(
        scope: str,
        max_requests: int,
        window_seconds: int
    ) -> Callable:
        async def dependency(request: Request, redis: RedisService = Depends(get_redis)):
            # 1. Determine unique identity partition
            auth_header = request.headers.get("Authorization")
            idem_header = request.headers.get("Idempotency-Key")

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                identifier = f"token:{token[-16:]}"
            elif idem_header and idem_header.strip():
                identifier = f"idem:{idem_header.strip()[:32]}"
            else:
                client_ip = request.headers.get("X-Forwarded-For")
                if client_ip:
                    identifier = f"ip:{client_ip.split(',')[0].strip()}"
                elif request.client:
                    identifier = f"ip:{request.client.host}"
                else:
                    identifier = "ip:unknown"

            key = f"rate_limit:{scope}:{identifier}"

            # 2. Check rate limit in Redis (or in-memory sliding window fallback)
            is_allowed, count, limit, retry_after = await redis.check_rate_limit(
                key=key,
                max_requests=max_requests,
                window_seconds=window_seconds
            )

            if not is_allowed:
                rate_limit_blocks_total.labels(scope=scope).inc()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests for {scope}. Limit is {limit} per {window_seconds}s.",
                    headers={"Retry-After": str(retry_after)}
                )

        return dependency
