import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_foreign_key_integrity_user_order(test_session: AsyncSession):
    """Verifies that orders cannot be created with a non-existent user_id."""
    await test_session.execute(text("PRAGMA foreign_keys = ON;"))
    invalid_order = Order(
        user_id=99999,  # Non-existent user ID
        total_amount=Decimal("150.00"),
        status="PENDING"
    )
    test_session.add(invalid_order)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_foreign_key_integrity_order_item_product(test_session: AsyncSession):
    """Verifies that order items cannot reference non-existent product IDs."""
    await test_session.execute(text("PRAGMA foreign_keys = ON;"))
    user = User(email="fk_test_user@example.com", hashed_password=get_password_hash("pass"))
    test_session.add(user)
    await test_session.flush()

    order = Order(user_id=user.id, total_amount=Decimal("50.00"), status="PENDING")
    test_session.add(order)
    await test_session.flush()

    invalid_item = OrderItem(
        order_id=order.id,
        product_id=88888,  # Non-existent product ID
        quantity=1,
        unit_price=Decimal("50.00")
    )
    test_session.add(invalid_item)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_inventory_check_constraint_stock_non_negative(test_session: AsyncSession):
    """Verifies that the database CHECK constraint rejects negative stock."""
    invalid_product = Product(
        title="Impossible GPU",
        price=Decimal("499.99"),
        stock=-5  # Violates CHECK (stock >= 0)
    )
    test_session.add(invalid_product)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_inventory_check_constraint_price_non_negative(test_session: AsyncSession):
    """Verifies that the database CHECK constraint rejects negative prices."""
    invalid_product = Product(
        title="Negative Price Item",
        price=Decimal("-10.00"),
        stock=10
    )
    test_session.add(invalid_product)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_order_item_quantity_check_constraint(test_session: AsyncSession):
    """Verifies that the database CHECK constraint rejects 0 or negative order quantities."""
    user = User(email="qty_test_user@example.com", hashed_password=get_password_hash("pass"))
    prod = Product(title="Valid Widget", price=Decimal("20.00"), stock=50)
    test_session.add_all([user, prod])
    await test_session.flush()

    order = Order(user_id=user.id, total_amount=Decimal("0.00"), status="PENDING")
    test_session.add(order)
    await test_session.flush()

    invalid_item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        quantity=0,  # Violates CHECK (quantity > 0)
        unit_price=Decimal("20.00")
    )
    test_session.add(invalid_item)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_user_email_unique_constraint(test_session: AsyncSession):
    """Verifies that duplicate emails are rejected at the database level."""
    u1 = User(email="duplicate_check@example.com", hashed_password=get_password_hash("pass1"))
    test_session.add(u1)
    await test_session.commit()

    u2 = User(email="duplicate_check@example.com", hashed_password=get_password_hash("pass2"))
    test_session.add(u2)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()

@pytest.mark.asyncio
async def test_cascade_delete_user_orders(test_session: AsyncSession):
    """Verifies that deleting a user cleanly cascades to delete their orders and order items."""
    user = User(email="cascade_user@example.com", hashed_password=get_password_hash("pass"))
    prod = Product(title="Cascade Widget", price=Decimal("15.00"), stock=20)
    test_session.add_all([user, prod])
    await test_session.flush()

    order = Order(user_id=user.id, total_amount=Decimal("15.00"), status="PENDING")
    test_session.add(order)
    await test_session.flush()

    item = OrderItem(order_id=order.id, product_id=prod.id, quantity=1, unit_price=Decimal("15.00"))
    test_session.add(item)
    await test_session.commit()

    # Delete User
    await test_session.delete(user)
    await test_session.commit()

    # Verify orders are deleted
    res_order = await test_session.execute(select(Order).where(Order.user_id == user.id))
    assert res_order.scalars().first() is None

    # Verify order items are deleted
    res_item = await test_session.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    assert res_item.scalars().first() is None

@pytest.mark.asyncio
async def test_transaction_rollback_preserves_initial_state(test_session: AsyncSession):
    """Verifies that uncommitted changes are rolled back on error."""
    prod = Product(title="Rollback Item", price=Decimal("100.00"), stock=10)
    test_session.add(prod)
    await test_session.commit()

    try:
        # Mutate stock in session
        prod.stock -= 2  # in-memory becomes 8
        # Add invalid entity to force failure
        test_session.add(User(email=None, hashed_password="pw"))  # NOT NULL violation
        await test_session.commit()
    except IntegrityError:
        await test_session.rollback()

    # Refresh and verify stock is still 10
    await test_session.refresh(prod)
    assert prod.stock == 10
