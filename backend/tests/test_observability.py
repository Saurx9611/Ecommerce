import pytest
from httpx import AsyncClient
from app.core.logging_config import sanitize_data

@pytest.mark.asyncio
async def test_request_and_correlation_id_generation(client: AsyncClient):
    """Verifies that all responses include generated X-Request-ID and X-Correlation-ID headers."""
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert "X-Correlation-ID" in resp.headers
    assert resp.headers["X-Request-ID"].startswith("req-")
    assert resp.headers["X-Correlation-ID"] == resp.headers["X-Request-ID"]

@pytest.mark.asyncio
async def test_custom_correlation_id_propagation(client: AsyncClient):
    """Verifies that client-supplied X-Request-ID and X-Correlation-ID headers are preserved."""
    custom_req_id = "custom-req-12345"
    custom_corr_id = "custom-corr-67890"

    resp = await client.get(
        "/healthz",
        headers={
            "X-Request-ID": custom_req_id,
            "X-Correlation-ID": custom_corr_id
        }
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_req_id
    assert resp.headers.get("X-Correlation-ID") == custom_corr_id

@pytest.mark.asyncio
async def test_health_and_readiness_probes(client: AsyncClient):
    """Verifies /healthz, /healthz/live, and /healthz/ready endpoints."""
    # 1. Healthz
    r1 = await client.get("/healthz")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    # 2. Liveness probe
    r2 = await client.get("/healthz/live")
    assert r2.status_code == 200
    assert r2.json()["status"] == "alive"

    # 3. Readiness probe
    r3 = await client.get("/healthz/ready")
    assert r3.status_code == 200
    data = r3.json()
    assert data["status"] == "ready"
    assert "database" in data["checks"]
    assert "redis" in data["checks"]

@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(client: AsyncClient):
    """Verifies that /metrics returns valid Prometheus exposition text with required application metrics."""
    await client.get("/healthz")

    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("Content-Type", "") or "version=0.0.4" in resp.headers.get("Content-Type", "")
    
    text = resp.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds" in text
    assert "orders_created_total" in text
    assert "payments_total" in text
    assert "inventory_reservations_total" in text
    assert "flash_sale_requests_total" in text
    assert "idempotency_operations_total" in text
    assert "rate_limit_blocks_total" in text

def test_log_sanitizer_security():
    """Verifies that passwords, tokens, JWTs, and card data are strictly redacted."""
    raw_payload = {
        "email": "customer@example.com",
        "password": "supersecretpassword123",
        "nested": {
            "token": "bearer-secret-token",
            "jwt": "eyJh...sensitive",
            "card_number": "4111111111111111",
            "cvv": "123",
            "safe_field": "public_data"
        }
    }
    sanitized = sanitize_data(raw_payload)
    assert sanitized["email"] == "customer@example.com"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["jwt"] == "[REDACTED]"
    assert sanitized["nested"]["card_number"] == "[REDACTED]"
    assert sanitized["nested"]["cvv"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "public_data"
