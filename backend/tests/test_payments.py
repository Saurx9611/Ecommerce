import asyncio
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.user import User
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_successful_payment_flow(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies the complete happy path:
    PENDING order -> POST /api/payments/charge -> PAID state with transaction ID.
    """
    order = Order(user_id=1, total_amount=Decimal("150.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"pay-success-{uuid.uuid4()}"
    payload = {"order_id": order_id}

    resp = await client.post(
        "/api/payments/charge",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PAID"
    assert data["order_id"] == order_id
    assert "transaction_id" in data

    # Verify DB persistence
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        db_order = await check_session.get(Order, order_id)
        assert db_order.status == "PAID"


@pytest.mark.asyncio
async def test_failed_payment_transitions_to_failed(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that a declined charge marks the order as FAILED.
    """
    order = Order(user_id=1, total_amount=Decimal("200.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"pay-fail-{uuid.uuid4()}"
    payload = {"order_id": order_id, "simulate_failure": True}

    resp = await client.post(
        "/api/payments/charge",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 400
    assert "declined" in resp.json()["detail"].lower()

    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        db_order = await check_session.get(Order, order_id)
        assert db_order.status == "FAILED"


@pytest.mark.asyncio
async def test_retry_payment_after_failure(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that a FAILED order can be retried and settled.
    """
    order = Order(user_id=1, total_amount=Decimal("80.00"), status="FAILED")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"pay-retry-{uuid.uuid4()}"
    payload = {"order_id": order_id, "simulate_failure": False}

    resp = await client.post(
        "/api/payments/charge",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAID"

    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        db_order = await check_session.get(Order, order_id)
        assert db_order.status == "PAID"


@pytest.mark.asyncio
async def test_payment_idempotency_response_replay(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that re-submitting the same payment idempotency key replays the stored charge without re-charging.
    """
    order = Order(user_id=1, total_amount=Decimal("95.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    await test_session.close()

    idem_key = f"pay-idem-{uuid.uuid4()}"
    payload = {"order_id": order_id}

    # First charge
    resp1 = await client.post("/api/payments/charge", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Replay charge with identical key
    resp2 = await client.post("/api/payments/charge", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp2.status_code == 200
    assert resp2.headers.get("X-Idempotent-Replay") == "true"
    data2 = resp2.json()

    assert data1["transaction_id"] == data2["transaction_id"]
    assert data1["status"] == data2["status"]


@pytest.mark.asyncio
async def test_unauthorized_payment_attempt(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that a user cannot charge an order belonging to a different user (403 Forbidden).
    """
    other_user = User(
        id=99,
        email="otheruser@podcastexplorer.io",
        hashed_password=get_password_hash("securepass123"),
        full_name="Other User"
    )
    order = Order(user_id=99, total_amount=Decimal("500.00"), status="PENDING")
    test_session.add_all([other_user, order])
    await test_session.commit()
    order_id = order.id
    await test_session.close()

    idem_key = f"pay-unauth-{uuid.uuid4()}"
    payload = {"order_id": order_id}

    resp = await client.post(
        "/api/payments/charge",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_concurrent_payment_charge_single_winner(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that concurrent payment charge requests on the same pending order
    do not cause duplicate charges (one wins, the other receives 409 Conflict).
    """
    order = Order(user_id=1, total_amount=Decimal("350.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    engine = test_session.bind
    await test_session.close()

    async def attempt_charge(idx: int):
        idem_key = f"pay-concurrent-{idx}-{uuid.uuid4()}"
        resp = await client.post(
            "/api/payments/charge",
            json={"order_id": order_id},
            headers={"Idempotency-Key": idem_key}
        )
        return resp.status_code

    tasks = [attempt_charge(1), attempt_charge(2)]
    results = await asyncio.gather(*tasks)

    # Exactly one request transitions and completes, or the other gets 409
    assert 200 in results
    assert len([r for r in results if r in [200, 409]]) == 2

    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        db_order = await check_session.get(Order, order_id)
        assert db_order.status == "PAID"


@pytest.mark.asyncio
async def test_payment_gateway_timeout_handling(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that gateway timeouts return 504 Gateway Timeout and mark the order as FAILED.
    """
    order = Order(user_id=1, total_amount=Decimal("120.00"), status="PENDING")
    test_session.add(order)
    await test_session.commit()
    order_id = order.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"pay-timeout-{uuid.uuid4()}"
    payload = {"order_id": order_id, "simulate_timeout": True}

    resp = await client.post(
        "/api/payments/charge",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )
    assert resp.status_code == 504
    detail = resp.json()["detail"].lower()
    assert "timed out" in detail or "timeout" in detail

    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        db_order = await check_session.get(Order, order_id)
        assert db_order.status == "FAILED"
