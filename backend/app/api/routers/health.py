import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_redis
from app.services.redis_service import RedisService
from app.core.metrics import export_metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Observability"])

@router.get("/healthz", summary="Basic service health")
async def health_check():
    return {
        "status": "ok",
        "service": "podcast-explorer-flash-sale",
        "version": "1.0.0"
    }

@router.get("/healthz/live", summary="Kubernetes Liveness Probe")
async def liveness_probe():
    return {"status": "alive"}

@router.get("/healthz/ready", summary="Kubernetes Readiness Probe with DB and Redis checks")
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis)
):
    db_healthy = False
    redis_healthy = False
    details = {}

    # 1. Probe Database Connectivity
    try:
        res = await db.execute(text("SELECT 1"))
        if res.scalar() == 1:
            db_healthy = True
            details["database"] = "connected"
    except Exception as e:
        logger.warning(f"Readiness check: Database probe failed: {e}")
        details["database"] = f"unhealthy: {str(e)}"

    # 2. Probe Redis Connectivity
    try:
        redis_ok = await redis.is_available()
        if redis_ok:
            redis_healthy = True
            details["redis"] = "connected"
        else:
            details["redis"] = "disconnected"
    except Exception as e:
        logger.warning(f"Readiness check: Redis probe failed: {e}")
        details["redis"] = f"unhealthy: {str(e)}"

    all_ready = db_healthy and redis_healthy
    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(
        content=f'{{"status": "{"ready" if all_ready else "not_ready"}", "checks": {details}}}'.replace("'", '"'),
        status_code=status_code,
        media_type="application/json"
    )

@router.get("/metrics", summary="Prometheus metrics exposition endpoint")
async def metrics_endpoint():
    data, content_type = export_metrics()
    return Response(content=data, media_type=content_type)
