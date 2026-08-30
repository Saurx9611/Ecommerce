import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.metrics import http_requests_total, http_request_duration_seconds

logger = logging.getLogger("app.access")

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware providing end-to-end distributed tracing IDs, structured JSON access logging,
    and automated Prometheus metrics observation across all HTTP endpoints.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Extract or generate Request and Correlation IDs
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        correlation_id = request.headers.get("X-Correlation-ID") or request_id

        # Attach to request state for downstream handlers
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(
                f"Unhandled exception processing {request.method} {request.url.path}: {e}",
                exc_info=True,
                extra={"request_id": request_id, "correlation_id": correlation_id}
            )
            raise e
        finally:
            duration_s = time.perf_counter() - start_time
            duration_ms = round(duration_s * 1000, 2)
            path = request.url.path

            # 2. Record Prometheus metrics (normalize parameterized paths)
            normalized_path = path
            if path.startswith("/api/episodes/"):
                normalized_path = "/api/episodes/{id}"
            elif path.startswith("/api/products/"):
                normalized_path = "/api/products/{id}"

            http_requests_total.labels(
                method=request.method,
                path=normalized_path,
                status_code=str(status_code)
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                path=normalized_path
            ).observe(duration_s)

            # 3. Structured access log
            logger.info(
                f"{request.method} {path} -> {status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "path": path,
                    "method": request.method,
                    "status_code": status_code,
                    "duration_ms": duration_ms
                }
            )

        # 4. Inject correlation headers into response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        return response
