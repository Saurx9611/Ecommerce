import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
from app.core.logging_config import setup_structured_logging
from app.middlewares.observability import ObservabilityMiddleware
import app.models  # Ensure all models are registered
from app.api.routers import (
    auth, episodes, search, projects, notifications,
    orders, payments, products, health
)
from app.services.websocket_service import manager

# Initialize JSON Structured Logging
setup_structured_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify database connection pool health
    async with engine.connect() as conn:
        try:
            await conn.execute(text("SELECT 1;"))
        except Exception as e:
            print(f"[CRITICAL] Database connection check failed: {e}")
    
    # Start Redis Pub/Sub listener background worker
    manager.start_background_tasks()
    
    yield
    
    # Shutdown: Stop background tasks and dispose engine connection pool cleanly
    await manager.stop_background_tasks()
    await engine.dispose()

app = FastAPI(
    title="Podcast Explorer Intelligence & Flash Sale API",
    description="AI-powered podcast intelligence engine and high-concurrency flash sale platform.",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Observability & Tracing Middleware
app.add_middleware(ObservabilityMiddleware)

# 2. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Health & Prometheus Metrics (root level /healthz, /healthz/ready, /healthz/live, /metrics)
app.include_router(health.router)

# 4. Include API Routers under /api
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(episodes.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)