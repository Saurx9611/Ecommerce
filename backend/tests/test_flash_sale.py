import pytest
import asyncio
import uuid
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.product import Product
from app.core.config import settings
from app.core.security import create_access_token
from app.services.redis_service import redis_service
from main import app

@pytest.mark.asyncio
async def test_flash_sale_prewarm_endpoint(client: AsyncClient, test_session: AsyncSession):
    # 1. Create a flash sale product
    product = Product(
        title="Flash Sale Ultimate Laptop",
        description="Limited Edition 100 units",
        price=Decimal("1999.00"),
        stock=100
    )
    test_session.add(product)
    await test_session.commit()
    await test_session.refresh(product)

    resp = await client.post(f"{settings.API_V1_STR}/products/{product.id}/prewarm")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "prewarmed"
    assert data["authoritative_stock"] == 100

@pytest.mark.asyncio
async def test_flash_sale_100_units_concurrency(client: AsyncClient, test_session: AsyncSession):
    """
    Simulates high-traffic flash sale: 10 units available with 25 concurrent buyers.
    Guarantees exactly 10 units purchased, 15 rejected, and DB stock ends at exactly 0.
    """
    product = Product(
        title="NVIDIA RTX 5090 GPU",
        description="Exclusive Drop",
        price=Decimal("1999.99"),
        stock=10
    )
    test_session.add(product)
    await test_session.commit()
    await test_session.refresh(product)

    # Prewarm Redis counter
    await redis_service.prewarm_stock(product.id, 10)

    # Create 25 unique registered users
    users = []
    for i in range(25):
        u = User(
            email=f"flash_buyer_{i}_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name=f"Buyer {i}"
        )
        test_session.add(u)
        users.append(u)
    await test_session.commit()

    tokens = [create_access_token({"sub": str(u.id)}) for u in users]

    async def attempt_checkout(token: str):
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": f"flash-rush-{uuid.uuid4()}"
        }
        payload = {
            "items": [{"product_id": product.id, "quantity": 1}]
        }
        return await client.post(
            f"{settings.API_V1_STR}/orders/flash-checkout",
            json=payload,
            headers=headers
        )

    # Fire all 25 concurrent checkout attempts simultaneously
    tasks = [attempt_checkout(token) for token in tokens]
    responses = await asyncio.gather(*tasks)

    successes = [r for r in responses if r.status_code == 201]
    rejections = [r for r in responses if r.status_code in [409, 410]]

    assert len(successes) == 10, f"Expected 10 successes, got {len(successes)}"
    assert len(rejections) == 15, f"Expected 15 rejections, got {len(rejections)}"

    # Authoritative DB verification
    await test_session.refresh(product)
    assert product.stock == 0, f"Authoritative stock must be 0, got {product.stock}"

@pytest.mark.asyncio
async def test_flash_sale_instant_rejection_when_sold_out(client: AsyncClient, test_session: AsyncSession):
    """
    Verifies that when stock is 0 in Redis, requests receive HTTP 410 Gone instantly.
    """
    product = Product(
        title="Sold Out Flagship Phone",
        description="0 stock",
        price=Decimal("999.00"),
        stock=0
    )
    test_session.add(product)
    await test_session.commit()
    await test_session.refresh(product)

    # Prewarm as 0
    await redis_service.prewarm_stock(product.id, 0)

    user = User(email=f"soldout_buyer_{uuid.uuid4().hex[:6]}@example.com", hashed_password="hash")
    test_session.add(user)
    await test_session.commit()
    token = create_access_token({"sub": str(user.id)})

    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": f"soldout-{uuid.uuid4()}"
    }
    payload = {"items": [{"product_id": product.id, "quantity": 1}]}
    resp = await client.post(
        f"{settings.API_V1_STR}/orders/flash-checkout",
        json=payload,
        headers=headers
    )
    assert resp.status_code in [409, 410]
