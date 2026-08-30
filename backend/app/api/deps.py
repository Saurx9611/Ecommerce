from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.services.redis_service import redis_service, RedisService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an isolated AsyncSession.
    Guarantees automatic rollback on unhandled exceptions and explicit session closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_redis() -> RedisService:
    """Dependency providing RedisService instance for admission control."""
    if not redis_service.client:
        await redis_service.connect()
    return redis_service

async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User | None:
    if not token:
        # Fallback to default developer/demo user if available
        res = await db.execute(select(User).order_by(User.id.asc()))
        user = res.scalars().first()
        if not user:
            from app.core.security import get_password_hash
            default_user = User(
                email="demo@podcastexplorer.io",
                hashed_password=get_password_hash("password123"),
                full_name="Podcast Explorer Demo"
            )
            db.add(default_user)
            await db.commit()
            await db.refresh(default_user)
            return default_user
        return user

    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
        
    try:
        user = await db.get(User, int(user_id))
        return user
    except Exception:
        return None

async def get_current_user(
    user: User | None = Depends(get_current_user_optional)
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user