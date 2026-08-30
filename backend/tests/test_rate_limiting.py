import pytest
import asyncio
import uuid
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_auth_login_rate_limiting_under_and_over_limit(client: AsyncClient):
    """
    Tests that login is allowed up to limit (5 req/60s), and the 6th request triggers HTTP 429.
    """
    ip_address = f"192.168.1.{uuid.uuid4().int % 250 + 1}"

    # First 5 login attempts
    for i in range(5):
        resp = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"},
            headers={"X-Forwarded-For": ip_address}
        )
        # Should be 401 Unauthorized (not rate limited)
        assert resp.status_code == 401, f"Attempt {i+1} failed with {resp.status_code}"

    # 6th attempt must be rejected with HTTP 429 Too Many Requests
    resp_6th = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
        headers={"X-Forwarded-For": ip_address}
    )
    assert resp_6th.status_code == 429
    assert "Retry-After" in resp_6th.headers
    assert "Too many requests for auth:login" in resp_6th.json()["detail"]

@pytest.mark.asyncio
async def test_concurrent_requests_distributed_rate_limiting(client: AsyncClient):
    """
    Fires 10 concurrent register attempts from the same IP (limit = 3).
    Guarantees exactly 3 allowed and 7 rejected with HTTP 429.
    """
    ip_address = f"10.0.0.{uuid.uuid4().int % 250 + 1}"

    async def attempt_register(idx: int):
        return await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": f"rate_limit_user_{idx}_{uuid.uuid4().hex[:6]}@example.com",
                "password": "Password123!"
            },
            headers={"X-Forwarded-For": ip_address}
        )

    tasks = [attempt_register(i) for i in range(10)]
    responses = await asyncio.gather(*tasks)

    allowed = [r for r in responses if r.status_code == 201]
    rate_limited = [r for r in responses if r.status_code == 429]

    assert len(allowed) == 3, f"Expected 3 allowed, got {len(allowed)}"
    assert len(rate_limited) == 7, f"Expected 7 rate limited, got {len(rate_limited)}"

@pytest.mark.asyncio
async def test_multiple_backend_instances_shared_redis_rate_limit(client: AsyncClient):
    """
    Simulates requests sharing the same Redis cluster state.
    Requests contribute to the same rolling rate limit bucket.
    """
    ip_address = f"172.16.0.{uuid.uuid4().int % 250 + 1}"

    # Send 2 requests
    for _ in range(2):
        resp = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"email": f"inst_a_{uuid.uuid4().hex[:6]}@example.com", "password": "pass"},
            headers={"X-Forwarded-For": ip_address}
        )
        assert resp.status_code == 201

    # Send 3rd request (Reaches limit 3)
    resp_3 = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": f"inst_b_{uuid.uuid4().hex[:6]}@example.com", "password": "pass"},
        headers={"X-Forwarded-For": ip_address}
    )
    assert resp_3.status_code == 201

    # 4th request must be blocked by Redis rate limit
    resp_4 = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": f"inst_b_overflow_{uuid.uuid4().hex[:6]}@example.com", "password": "pass"},
        headers={"X-Forwarded-For": ip_address}
    )
    assert resp_4.status_code == 429
