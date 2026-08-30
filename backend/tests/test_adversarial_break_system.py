import asyncio
import uuid
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.idempotency import IdempotencyRecord
from app.core.config import settings
from app.core.security import get_password_hash
from app.services.redis_service import redis_service
from app.services.idempotency_service import IdempotencyService
from app.api.routers.orders import CreateOrderRequest

# =============================================================================
# 1. ADVERSARIAL AUTH ATTACK VECTORS
# =============================================================================

@pytest.mark.asyncio
async def test_adversarial_forged_jwt_token(client: AsyncClient):
    """Attack: Attacker crafts a forged JWT signed with an arbitrary malicious key."""
    forged_token = jwt.encode(
        {"sub": "1", "email": "admin@podcastexplorer.io", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "malicious-attacker-secret-key",
        algorithm="HS256"
    )
    resp = await client.get("/api/orders/", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp.status_code == 401
    assert "could not validate credentials" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_adversarial_expired_jwt_token(client: AsyncClient):
    """Attack: Attacker attempts to replay an expired session token."""
    expired_token = jwt.encode(
        {"sub": "1", "email": "test@podcastexplorer.io", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp = await client.get("/api/orders/", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_adversarial_cross_user_order_hijacking(client: AsyncClient, test_session: AsyncSession):
    """Attack: User 1 attempts to access User 2's private order."""
    user2 = User(id=2, email="victim@podcastexplorer.io", hashed_password=get_password_hash("pass"), full_name="Victim")
    order2 = Order(user_id=2, total_amount=Decimal("1500.00"), status="PAID")
    test_session.add_all([user2, order2])
    await test_session.commit()
    victim_order_id = order2.id
    await test_session.close()

    # User 1 (authenticated in client fixture) tries to fetch User 2's order
    resp = await client.get(f"/api/orders/{victim_order_id}")
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"].lower()

# =============================================================================
# 2. ADVERSARIAL IDEMPOTENCY & CONCURRENCY ATTACK VECTORS
# =============================================================================

@pytest.mark.asyncio
async def test_adversarial_concurrent_idempotency_race(client: AsyncClient, test_session: AsyncSession):
    """Attack: Two threads submit the same Idempotency-Key simultaneously."""
    prod = Product(title="Race Test Item", price=Decimal("80.00"), stock=5)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    await test_session.close()

    shared_idem_key = f"key-race-{uuid.uuid4()}"
    payload = {"items": [{"product_id": prod_id, "quantity": 1}]}

    async def hit():
        return await client.post(
            "/api/orders/flash-checkout",
            json=payload,
            headers={"Idempotency-Key": shared_idem_key, "X-Forwarded-For": "10.9.9.9"}
        )

    r1, r2 = await asyncio.gather(hit(), hit())
    status_codes = [r1.status_code, r2.status_code]
    
    # Invariant: One must succeed (201) or replay (201/200), and the other must not double charge (either 201 replay or 409 conflict)
    assert 201 in status_codes
    assert all(s in [201, 200, 409] for s in status_codes)

@pytest.mark.asyncio
async def test_adversarial_stale_cache_recovery_on_cache_miss(client: AsyncClient, test_session: AsyncSession):
    """Attack: Redis cache is completely cold (evicted / restarted) during flash sale."""
    prod = Product(title="Cold Cache Item", price=Decimal("120.00"), stock=3)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    await test_session.close()

    # Ensure Redis has no cache entry for this item (cold start)
    key = f"product:{prod_id}:stock"
    if key in redis_service._memory_store:
        del redis_service._memory_store[key]

    # Attempt checkout on un-cached product
    idem_key = f"key-cold-{uuid.uuid4()}"
    payload = {"items": [{"product_id": prod_id, "quantity": 1}]}
    
    resp = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp.status_code == 201
    assert resp.json()["status"] == "PAID"

# =============================================================================
# 3. ADVERSARIAL PAYMENT ATTACK VECTORS
# =============================================================================

@pytest.mark.asyncio
async def test_adversarial_double_click_payment_protection(client: AsyncClient, test_session: AsyncSession):
    """Attack: Rapid double-click on payment submit button with identical key."""
    order = Order(user_id=1, total_amount=Decimal("200.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    await test_session.close()

    idem_key = f"key-double-click-{uuid.uuid4()}"
    payload = {"order_id": order_id}

    async def click():
        return await client.post(
            "/api/payments/charge",
            json=payload,
            headers={"Idempotency-Key": idem_key, "X-Forwarded-For": "10.5.5.5"}
        )

    resp1, resp2 = await asyncio.gather(click(), click())
    # One succeeds, second replays or blocks
    assert 200 in [resp1.status_code, resp2.status_code]
    assert all(s in [200, 409] for s in [resp1.status_code, resp2.status_code])
