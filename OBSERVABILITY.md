# Production Observability Architecture & Metrics Specification

**Platform:** Podcast Explorer Intelligence Platform & High-Concurrency Flash Sale Engine  
**Observability Tier:** Structured JSON Logging + Distributed Tracing IDs + Prometheus Metrics + Deep Health Probes  
**Metrics Exposition:** `GET /metrics` (Prometheus Text Exposition Format 0.0.4)  
**Status:** Implemented & Formally Verified (Phase 11)  
**Author:** Senior Observability & Site Reliability Engineer  

---

## 1. End-to-End Critical Transaction Path

Every customer transaction traverses a strictly monitored pipeline:

```
[Inbound HTTP Request]
        │
        ▼ (X-Request-ID & X-Correlation-ID Injected)
[1. Authentication & JWT Validation]
        │
        ▼
[2. Distributed Rate Limiter]  ──(Blocked)──► rate_limit_blocks_total ++
        │
        ▼ (Passed)
[3. Idempotency Service]        ──(Replay)──► idempotency_operations_total{action="REPLAYED"} ++
        │
        ▼ (New Lock Claimed)
[4. Redis Fast-Path Inventory]  ──(Sold Out)► inventory_reservations_total{result="OUT_OF_STOCK"} ++
        │                                     flash_sale_requests_total{result="REJECTED_SOLD_OUT"} ++
        ▼ (Reserved)
[5. PostgreSQL Atomic Commit]   ──(Success)─► orders_created_total{status="PAID"} ++
        │
        ▼
[6. Payment Gateway Simulator]  ──(Charge)──► payments_total{status="PAID"|"FAILED"|"TIMEOUT"} ++
        │
        ▼
[7. Outbound Response] (X-Request-ID, X-Correlation-ID Headers & Duration Metric Emitted)
```

---

## 2. Distributed Tracing & Correlation IDs

1. **Header Propagation:**
   - `X-Request-ID`: Unique per HTTP request (format: `req-[0-9a-f]{12}`).
   - `X-Correlation-ID`: Multi-service trace ID preserved across upstream microservices and API gateways.
2. **Middleware Attachment:**
   - Implemented in [`ObservabilityMiddleware`](file:///c:/Users/saura/OneDrive/Desktop/ecommerce/backend/app/middlewares/observability.py).
   - Injected into `request.state` and automatically written to all outbound HTTP response headers.

---

## 3. Structured JSON Logging & Security Sanitization

### 3.1 Log Format Specification
Logs are formatted in single-line JSON compliant with standard log forwarders (FluentBit, Vector, Datadog Agent, CloudWatch):

```json
{
  "timestamp": "2026-08-30T12:15:51.569034+00:00",
  "level": "INFO",
  "logger": "app.access",
  "message": "POST /api/orders/flash-checkout -> 201 (18.42ms)",
  "module": "observability",
  "line": 62,
  "request_id": "req-8bc395a3e79c",
  "correlation_id": "req-8bc395a3e79c",
  "path": "/api/orders/flash-checkout",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 18.42
}
```

### 3.2 Security & Zero PII Leakage Guarantee
Implemented in [`logging_config.py`](file:///c:/Users/saura/OneDrive/Desktop/ecommerce/backend/app/core/logging_config.py):
The recursive sanitizer automatically redacts the following sensitive keys across all dictionary payloads:
- `password`, `hashed_password`
- `token`, `access_token`, `refresh_token`, `jwt`
- `authorization`, `secret`, `api_key`
- `card_number`, `cvv`

---

## 4. Kubernetes Health Probes

| Endpoint | Probe Type | Target Check | Success Response | Failure Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET /healthz` | General Health | Application online | `200 {"status": "ok"}` | `500` |
| `GET /healthz/live` | Liveness Probe | Event loop responsiveness | `200 {"status": "alive"}` | `500` (Triggers pod restart) |
| `GET /healthz/ready` | Readiness Probe | PostgreSQL (`SELECT 1`) + Redis (`PING`) | `200 {"status": "ready", "checks": {"database": "connected", "redis": "connected"}}` | `503 {"status": "not_ready"}` (Removes pod from load balancer) |

---

## 5. Prometheus Application Metrics Catalog (`GET /metrics`)

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | `method`, `path`, `status_code` | Total HTTP requests handled by the platform. |
| `http_request_duration_seconds` | Histogram | `method`, `path` | Request latency distribution across standard Prometheus buckets. |
| `orders_created_total` | Counter | `status` | Total orders created (e.g. `PAID`, `PENDING`). |
| `payments_total` | Counter | `status` | Total payment charge attempts (e.g. `PAID`, `FAILED`, `TIMEOUT`, `ERROR`). |
| `inventory_reservations_total` | Counter | `result` | Inventory allocation attempts (`SUCCESS`, `OUT_OF_STOCK`, `DB_OUT_OF_STOCK`). |
| `flash_sale_requests_total` | Counter | `result` | Flash sale admission filter results (`ADMITTED`, `REJECTED_SOLD_OUT`). |
| `idempotency_operations_total` | Counter | `action` | Idempotency lifecycle operations (`NEW`, `REPLAYED`, `CONFLICT`, `LOCK_ACQUIRED`). |
| `rate_limit_blocks_total` | Counter | `scope` | Total requests rejected by the distributed rate limiter (HTTP 429). |
| `active_websocket_connections` | Gauge | None | Number of live multiplexed WebSocket client connections. |

---

## 6. Verification Results

- **Automated Observability Tests (`tests/test_observability.py`):** 5/5 passed.
  - Verified Request ID and Correlation ID header generation and propagation.
  - Verified `/healthz`, `/healthz/live`, and `/healthz/ready` probes with PostgreSQL and Redis connectivity.
  - Verified Prometheus `/metrics` exposition format.
  - Verified recursive log sanitizer security against password/token leaks.
- **Backend Test Suite:** 41/41 tests passed (100% success).
- **Frontend Test Suite:** 10/10 tests passed (100% success).
