from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# 1. HTTP Ingress & Latency Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "path", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency distribution in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 2. Transactional & Order Metrics
orders_created_total = Counter(
    "orders_created_total",
    "Total orders created across the platform",
    ["status"]  # e.g., 'PAID', 'PENDING'
)

# 3. Payment Gateway Metrics
payments_total = Counter(
    "payments_total",
    "Total payment transactions attempted",
    ["status"]  # e.g., 'SUCCESS', 'FAILED', 'TIMEOUT'
)

# 4. Inventory Reservation & Concurrency Metrics
inventory_reservations_total = Counter(
    "inventory_reservations_total",
    "Total inventory reservation attempts",
    ["result"]  # e.g., 'SUCCESS', 'OUT_OF_STOCK', 'BATCH_FAILED'
)

# 5. Flash Sale Engine Metrics
flash_sale_requests_total = Counter(
    "flash_sale_requests_total",
    "Total flash sale checkout requests processed",
    ["result"]  # e.g., 'ADMITTED', 'REJECTED_SOLD_OUT', 'REJECTED_RATE_LIMITED'
)

# 6. Idempotency Metrics
idempotency_operations_total = Counter(
    "idempotency_operations_total",
    "Total idempotency key lifecycle checks",
    ["action"]  # e.g., 'NEW', 'REPLAYED', 'CONFLICT', 'LOCK_ACQUIRED'
)

# 7. Rate Limiter Metrics
rate_limit_blocks_total = Counter(
    "rate_limit_blocks_total",
    "Total requests throttled by distributed rate limiter",
    ["scope"]  # e.g., 'auth:login', 'orders:flash_sale'
)

# 8. Active Real-Time WebSocket Gauges
active_websocket_connections = Gauge(
    "active_websocket_connections",
    "Current active multiplexed WebSocket client connections"
)

def export_metrics() -> tuple[bytes, str]:
    """Generates Prometheus text exposition payload."""
    return generate_latest(), CONTENT_TYPE_LATEST
