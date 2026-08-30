import json
import logging
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.api.deps import get_db, get_redis
from app.models.product import Product
from app.services.redis_service import RedisService
from app.services.websocket_service import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    stock: int

class ProductResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    stock: int

@router.get("/", response_model=List[ProductResponse], status_code=status.HTTP_200_OK)
async def list_products(db: AsyncSession = Depends(get_db)):
    """Fetch the entire authoritative product catalog from PostgreSQL."""
    result = await db.execute(select(Product).order_by(Product.id.asc()))
    products = result.scalars().all()
    return [
        ProductResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            price=float(p.price),
            stock=p.stock
        )
        for p in products
    ]

@router.get("/categories/summary", status_code=status.HTTP_200_OK)
async def get_categories_summary(db: AsyncSession = Depends(get_db)):
    """Summary of product count and inventory."""
    res = await db.execute(select(func.count(Product.id), func.sum(Product.stock)))
    count, total_stock = res.first()
    return {
        "categories": [
            {"id": 1, "name": "Flash Sale Hardware", "count": count or 0, "stock": total_stock or 0}
        ],
        "total_products": count or 0,
        "total_stock": total_stock or 0
    }

@router.get("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve single product details."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found."
        )
    return ProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        price=float(product.price),
        stock=product.stock
    )

@router.post("/{product_id}/prewarm", status_code=status.HTTP_200_OK)
async def prewarm_flash_sale_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis)
):
    """
    Pre-warms authoritative PostgreSQL stock into Redis admission counter ahead of a flash sale.
    """
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found."
        )
    await redis.prewarm_stock(product.id, product.stock)
    await manager.broadcast_stock_update(product.id, product.stock)
    return {
        "status": "prewarmed",
        "product_id": product.id,
        "authoritative_stock": product.stock,
        "cache_key": f"product:{product.id}:stock"
    }

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis)
):
    product = Product(
        title=payload.title,
        description=payload.description,
        price=Decimal(str(payload.price)),
        stock=payload.stock
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    # Prewarm Redis stock
    await redis.prewarm_stock(product.id, product.stock)
    await manager.broadcast_stock_update(product.id, product.stock)
    return ProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        price=float(product.price),
        stock=product.stock
    )

@router.websocket("/ws/stock")
async def websocket_stock_endpoint(websocket: WebSocket):
    """
    Multiplexed Single-WebSocket endpoint supporting subscribe, unsubscribe, and heartbeat ping/pong.
    """
    await manager.connect(websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
                action = msg.get("action")
                
                if action == "subscribe":
                    product_ids = msg.get("product_ids", [])
                    if isinstance(product_ids, list):
                        manager.subscribe(websocket, product_ids)
                        await websocket.send_text(json.dumps({
                            "type": "SUBSCRIPTION_ACK",
                            "subscribed_ids": product_ids
                        }))

                elif action == "unsubscribe":
                    product_ids = msg.get("product_ids", [])
                    if isinstance(product_ids, list):
                        manager.unsubscribe(websocket, product_ids)

                elif action == "ping":
                    await websocket.send_text(json.dumps({"type": "PONG"}))

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client closed with exception: {e}")
        manager.disconnect(websocket)