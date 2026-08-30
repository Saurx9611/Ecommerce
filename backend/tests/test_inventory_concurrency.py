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

@pytest.mark.asyncio
async def test_high_concurrency_single_stock_oversell_prevention(client: AsyncClient, test_session: AsyncSession):
    """
    Test: 100 concurrent buyers competing for 1 unit of stock.
    Invariant: Exactly 1 order succeeds, 99 fail with 409/410. Final stock == 0.
    """
    # 1. Create limited flash sale item
    product = Product(
        title="Ultra Rare GPU",
        description="Exclusive flash sale item",
        price=Decimal("999.00"),
        stock=1
    )
    test_session.add(product)
    await test_session.commit()
    product_id = product.id
    engine = test_session.bind
    await test_session.close()

    # 2. Fire 100 concurrent checkout requests
    num_concurrent = 100

    async def attempt_checkout(idx: int):
        idem_key = f"idem-gpu-{idx}-{uuid.uuid4()}"
        payload = {
            "items": [{"product_id": product_id, "quantity": 1}]
        }
        resp = await client.post(
            "/api/orders/flash-checkout",
            json=payload,
            headers={"Idempotency-Key": idem_key}
        )
        return resp.status_code

    tasks = [attempt_checkout(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)

    # 3. Analyze results
    success_count = results.count(201)
    rejected_count = results.count(409) + results.count(410)

    assert success_count == 1, f"Expected exactly 1 successful purchase, got {success_count}"
    assert rejected_count == 99, f"Expected 99 rejections, got {rejected_count}"

    # 4. Verify durable database state
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        res = await check_session.execute(select(Product.stock).where(Product.id == product_id))
        final_stock = res.scalar_one()
        assert final_stock == 0, f"Expected final stock to be 0, got {final_stock}"

        res_orders = await check_session.execute(
            select(OrderItem).where(OrderItem.product_id == product_id)
        )
        orders = res_orders.scalars().all()
        assert len(orders) == 1


@pytest.mark.asyncio
async def test_high_concurrency_ten_stock_hundred_buyers(client: AsyncClient, test_session: AsyncSession):
    """
    Test: 100 concurrent buyers competing for 10 units of stock.
    Invariant: Exactly 10 orders succeed, 90 fail. Final stock == 0.
    """
    product = Product(
        title="High Demand Phone",
        price=Decimal("499.00"),
        stock=10
    )
    test_session.add(product)
    await test_session.commit()
    product_id = product.id
    engine = test_session.bind
    await test_session.close()

    num_concurrent = 100

    async def attempt_checkout(idx: int):
        idem_key = f"idem-phone-{idx}-{uuid.uuid4()}"
        payload = {
            "items": [{"product_id": product_id, "quantity": 1}]
        }
        resp = await client.post(
            "/api/orders/flash-checkout",
            json=payload,
            headers={"Idempotency-Key": idem_key}
        )
        return resp.status_code

    tasks = [attempt_checkout(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)

    success_count = results.count(201)
    rejected_count = results.count(409) + results.count(410)

    assert success_count == 10, f"Expected exactly 10 successful purchases, got {success_count}"
    assert rejected_count == 90, f"Expected 90 rejections, got {rejected_count}"

    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        res = await check_session.execute(select(Product.stock).where(Product.id == product_id))
        final_stock = res.scalar_one()
        assert final_stock == 0, f"Expected final stock to be 0, got {final_stock}"


@pytest.mark.asyncio
async def test_multi_item_atomic_checkout_all_or_nothing(client: AsyncClient, test_session: AsyncSession):
    """
    Test: Multi-item checkout where item A has stock (5), but item B has 0.
    Invariant: Entire checkout must fail. Item A stock must NOT be decremented.
    """
    prod_a = Product(title="In-Stock Keyboard", price=Decimal("100.00"), stock=5)
    prod_b = Product(title="Out-of-Stock Mouse", price=Decimal("50.00"), stock=0)
    test_session.add_all([prod_a, prod_b])
    await test_session.commit()
    prod_a_id = prod_a.id
    prod_b_id = prod_b.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"idem-multi-{uuid.uuid4()}"
    payload = {
        "items": [
            {"product_id": prod_a_id, "quantity": 1},
            {"product_id": prod_b_id, "quantity": 1}
        ]
    }

    resp = await client.post(
        "/api/orders/flash-checkout",
        json=payload,
        headers={"Idempotency-Key": idem_key}
    )

    assert resp.status_code in [409, 410]

    # Verify Prod A stock was NOT decremented
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        res = await check_session.execute(select(Product.stock).where(Product.id == prod_a_id))
        final_stock_a = res.scalar_one()
        assert final_stock_a == 5, f"Expected Product A stock to remain 5, but got {final_stock_a}"


@pytest.mark.asyncio
async def test_idempotent_duplicate_checkout(client: AsyncClient, test_session: AsyncSession):
    """
    Test: Submitting the same idempotency key multiple times.
    Invariant: Only 1 order created, 1 stock decremented, identical response returned.
    """
    prod = Product(title="Idempotent Item", price=Decimal("25.00"), stock=5)
    test_session.add(prod)
    await test_session.commit()
    prod_id = prod.id
    engine = test_session.bind
    await test_session.close()

    idem_key = f"idem-fixed-key-{uuid.uuid4()}"
    payload = {"items": [{"product_id": prod_id, "quantity": 2}]}

    # First request
    resp1 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp1.status_code == 201
    order1 = resp1.json()

    # Second request with identical key
    resp2 = await client.post("/api/orders/flash-checkout", json=payload, headers={"Idempotency-Key": idem_key})
    assert resp2.status_code == 201
    order2 = resp2.json()

    assert order1["order_id"] == order2["order_id"]
    assert order1["total_amount"] == order2["total_amount"]

    # Stock should only be decremented once (5 - 2 = 3)
    async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_factory() as check_session:
        res = await check_session.execute(select(Product.stock).where(Product.id == prod_id))
        final_stock = res.scalar_one()
        assert final_stock == 3
