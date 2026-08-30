# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for ultra-fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install Python dependencies into virtual environment
COPY pyproject.toml uv.lock ./
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen --no-dev

# Stage 2: Production Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

# Runtime libraries (PostgreSQL client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root system user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application source code
COPY . .
RUN chmod +x /app/docker-entrypoint.sh
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check probing Kubernetes readiness probe
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/healthz/ready || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
