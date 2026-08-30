import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.idempotency import IdempotencyRecord
from app.api.routers.orders import CreateOrderRequest
from app.services.redis_service import redis_service

@pytest.mark.asyncio
async def test_idempotency_key_validation_missing_or_invalid(client: AsyncClient):
    """Verifies that missing or invalid format Idempotency-Key headers are rejected with 400."""
    payload = {"items": [{"product_id": 1, "quantity": 1}]}

    # Missing header
    r_missing = await client.post("/api/orders/flash-checkout", json=payload)
    assert r_missing.status_code == 422 or r_missing.status_code == 400

    # Empty whitespace header
    r_empty = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": "   "})
    assert r_empty.status_code == 400

    # Header with invalid symbols
    r_invalid = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": "key with spaces!@#"})
    assert r_invalid.status_code == 400


@pytest.mark.asyncio
async def test_mismatched_payload_fingerprint_conflict(client: AsyncClient, test_session: AsyncSession):
    """Verifies that reusing the same key with different payload is rejected with 409 Conflict."""
    prod = Product(title="Fingerprint Test Item", price=Decimal("50.00"), stock=10)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    await test_session.close()

    idem_key = f"key-fp-{uuid.uuid4()}"

    # Request A
    payload_a = {"items": [{"product_id": prod_id, "quantity": 1}]}
    resp_a = await client.post("/api/orders/flash-checkout", json=payload_a, headers={"Idempotency-Key": idem_key})
    assert resp_a.status_code == 201

    # Request B (Same key, different quantity)
    payload_b = {"items": [{"product_id": prod_id, "quantity": 2}]}
    resp_b = await client.post("/api/orders/flash-checkout", json=payload_b, headers={"Idempotency-Key": idem_key})
    assert resp_b.status_code == 409
    assert "mismatched" in resp_b.json()["detail"].lower()


@pytest.mark.asyncio
async def test_completed_response_replay_header(client: AsyncClient, test_session: AsyncSession):
    """Verifies that completed requests are replayed with identical body and X-Idempotent-Replay header."""
    prod = Product(title="Replay Test Item", price=Decimal("75.00"), stock=10)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"key-replay-{uuid.uuid4()}"
    payload = {"items": [{"product_id": prod_id, "quantity": 1}]}

    # First attempt
    resp1 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp1.status_code == 201
    assert "X-Idempotent-Replay" not in resp1.headers
    data1 = resp1.json()

    # Replay attempt
    resp2 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp2.status_code == 201 or resp2.status_code == 200
    assert resp2.headers.get("X-Idempotent-Replay") == "true"
    data2 = resp2.json()

    assert data1["order_id"] == data2["order_id"]
    assert data1["total_amount"] == data2["total_amount"]

    # Verify stock decremented only once (10 - 1 = 9)
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        res = await check_session.execute(select(Product.stock).where(Product.id == prod_id))
        assert res.scalar_one() == 9


@pytest.mark.asyncio
async def test_retry_after_failed_request(client: AsyncClient, test_session: AsyncSession):
    """Verifies that a failed request transitions out of IN_PROGRESS and allows subsequent retry."""
    prod = Product(title="Initially Out-of-Stock Item", price=Decimal("30.00"), stock=0)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"key-retry-{uuid.uuid4()}"
    payload = {"items": [{"product_id": prod_id, "quantity": 1}]}

    # First attempt fails due to stock = 0
    resp1 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp1.status_code in [409, 410]

    # Replenish stock in DB and prewarm cache
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as replenish_session:
        prod_obj = await replenish_session.get(Product, prod_id)
        prod_obj.stock = 5
        await replenish_session.commit()

    await redis_service.prewarm_stock(prod_id, 5)

    # Second attempt with same key now succeeds
    resp2 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp2.status_code == 201
    assert resp2.json()["status"] == "PAID"


@pytest.mark.asyncio
async def test_crash_recovery_expired_in_progress_lock(client: AsyncClient, test_session: AsyncSession):
    """Verifies that a stalled/crashed IN_PROGRESS record with an expired lock is safely recoverable."""
    prod = Product(title="Crash Recovery Item", price=Decimal("40.00"), stock=5)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id

    idem_key = f"key-crash-{uuid.uuid4()}"
    req_obj = CreateOrderRequest(items=[{"product_id": prod_id, "quantity": 1}])
    payload_dump = req_obj.model_dump()

    # Simulate an orphaned IN_PROGRESS record from a crashed worker 60s ago
    from app.services.idempotency_service import IdempotencyService
    req_hash = IdempotencyService.compute_fingerprint("POST", "/api/orders/flash-checkout", 1, payload_dump)
    
    stalled_record = IdempotencyRecord(
        idempotency_key=idem_key,
        user_id=1,
        request_hash=req_hash,
        status="IN_PROGRESS",
        locked_until=datetime.now(timezone.utc) - timedelta(seconds=60)  # Expired
    )
    test_session.add(stalled_record)
    await test_session.commit()
    await test_session.close()

    # Retry should detect expired lock and complete successfully
    resp = await client.post("/api/orders/flash-checkout", json=payload_dump, headers={"Idempotency-Key": idem_key})
    assert resp.status_code == 201
    assert resp.json()["status"] == "PAID"
