from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, func, CheckConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="chk_products_stock_non_negative"),
        CheckConstraint("price >= 0", name="chk_products_price_non_negative"),
        Index("idx_products_title", "title"),
        Index("idx_products_price", "price"),
    )