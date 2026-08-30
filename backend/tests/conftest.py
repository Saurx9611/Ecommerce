import os
import tempfile
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.api.deps import get_db
from app.models.user import User
from app.core.security import get_password_hash
from app.services.redis_service import redis_service
from main import app

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
def reset_redis_emulator():
    redis_service._memory_zsets.clear()
    redis_service._memory_store.clear()
    yield
    redis_service._memory_zsets.clear()
    redis_service._memory_store.clear()

@pytest_asyncio.fixture
async def test_engine():
    # File-based isolated SQLite DB allowing true multi-connection isolation
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 30.0},
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def client(test_engine):
    async_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    
    # Create test user for this isolated test DB
    async with async_session_factory() as session:
        test_user = User(
            id=1,
            email=f"tester_{uuid.uuid4().hex[:6]}@podcastexplorer.io",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test Architect"
        )
        session.add(test_user)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
