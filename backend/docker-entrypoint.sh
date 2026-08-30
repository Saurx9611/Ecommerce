#!/bin/sh
set -e

echo "[STARTUP] Running database schema migrations (Alembic)..."
alembic upgrade head

echo "[STARTUP] Launching FastAPI Uvicorn Server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-2}
