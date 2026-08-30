# Real-Time Stock Architecture & Cross-Instance Event Propagation

**Platform:** Podcast Explorer Intelligence Platform & High-Concurrency Flash Sale Engine  
**Protocols:** WebSocket (RFC 6455), Redis Pub/Sub, JSON-RPC-style Multiplexing  
**Authoritative Source of Truth:** PostgreSQL 16 (Durable ACID Store)  
**Status:** Implemented & Formally Verified (Phase 7)  

---

## 1. Executive Summary

This document specifies the transition from an unscalable **1-WebSocket-per-product** architecture to a production-grade **Single-Connection Multiplexed Real-Time Architecture** backed by **Redis Pub/Sub cross-instance fanout**.

```
                           OLD ARCHITECTURE (Unscalable)
  [ProductCard 1] ─── WS Connection 1 ───┐
  [ProductCard 2] ─── WS Connection 2 ───┼──> [FastAPI Instance A] (Local Python list)
  [ProductCard N] ─── WS Connection N ───┘    * Instance B and C receive NO updates.
                                               * Exhausts browser socket & file descriptor limits.

                          NEW ARCHITECTURE (Multiplexed & Distributed)
  [Browser / Page] 
         │ (ONE Single Multiplexed WebSocket Connection)
         ▼
  [StockWebSocketProvider] ───> [/api/products/ws/stock]
         ▲
         │ (Redis Pub/Sub Channel: "channel:stock_updates")
  ┌──────┴────────────────────────┬────────────────────────┐
  ▼                               ▼                        ▼
[FastAPI Instance A]     [FastAPI Instance B]     [FastAPI Instance C]
  └─ Local clients         └─ Local clients         └─ Local clients
```

---

## 2. Architectural Comparison

| Dimension | Old Architecture | New Production Architecture |
| :--- | :--- | :--- |
| **Browser Socket Count** | $N$ connections (1 per mounted card) | **$1$ connection per browser window/tab** |
| **Multiplexing** | None (1 product per socket) | **Bidirectional dynamic subscribe / unsubscribe JSON messages** |
| **Cross-Instance Sync** | ❌ None (In-memory Python list) | **✅ Redis Pub/Sub (`channel:stock_updates`) fanout** |
| **Reconnection Strategy** | None / Naive reload | **Exponential backoff with jitter + automatic resubscription** |
| **Heartbeat / Liveness** | None | **Client ping every 25s $\rightarrow$ Server `PONG` acknowledgment** |
| **Authoritative Role** | Ambiguous | **Strictly informational; PostgreSQL remains single source of truth** |

---

## 3. Multiplexed Protocol Specification

Clients communicate over a single persistent WebSocket at `ws://<host>:<port>/api/products/ws/stock`.

### 3.1 Client $\rightarrow$ Server Frame Types

#### 1. Subscribe to Product IDs
```json
{
  "action": "subscribe",
  "product_ids": [1, 2, 3, 42]
}
```
*Response from Server:*
```json
{
  "type": "SUBSCRIPTION_ACK",
  "subscribed_ids": [1, 2, 3, 42]
}
```

#### 2. Unsubscribe from Product IDs
```json
{
  "action": "unsubscribe",
  "product_ids": [42]
}
```

#### 3. Heartbeat Ping
```json
{
  "action": "ping"
}
```
*Response from Server:*
```json
{
  "type": "PONG"
}
```

### 3.2 Server $\rightarrow$ Client Frame Types

#### Real-Time Stock Update Notification
```json
{
  "type": "STOCK_UPDATE",
  "product_id": 1,
  "stock": 4
}
```

---

## 4. Cross-Instance Redis Pub/Sub Flow

When an order is placed on any node (e.g. Instance A):
1. **Durable Commit:** PostgreSQL executes atomic conditional decrement and commits.
2. **Local Fast-Path:** Instance A immediately notifies any local WebSockets subscribed to that product.
3. **Redis Pub/Sub Publish:** Instance A publishes `{"product_id": 1, "stock": 4}` to Redis channel `channel:stock_updates`.
4. **Cross-Node Distribution:** All running FastAPI instances (Instance B, Instance C, ...) listening on the Pub/Sub channel receive the message and forward it to their locally connected WebSockets.

---

## 5. Resilience & Failure Recovery

1. **Informational Invariant:** WebSocket notifications are **advisory only**. If a client experiences network disruption or misses a frame:
   - On checkout attempt, PostgreSQL unconditionally verifies stock atomically (`UPDATE products SET stock = stock - :qty WHERE id = :id AND stock >= :qty`).
   - If stock is exhausted, the server rejects the order with `409 Conflict` / `410 Gone`.
2. **Exponential Backoff Reconnect:**
   $$\text{Delay} = \min(1000 \times 1.5^{\text{attempts}}, 15000) + \text{random}(0, 500)\text{ ms}$$
3. **State Resynchronization:**
   Upon WebSocket reconnection (`onopen`), the provider automatically resubscribes all active product IDs registered across mounted components.

---

## 6. Verification Results

- **Vitest Provider & Multiplexing Test:** `tests/stock_websocket.test.ts` verified that multiple components subscribe to different products over exactly 1 WebSocket instance and receive discrete live stock events.
- **Backend Redis Pub/Sub Worker:** Integrated in `FastAPI lifespan` startup/shutdown without dangling tasks.
- **Pytest Suite:** 30/30 tests passed with 100% success.
- **Next.js Production Build:** 10/10 routes compiled cleanly (`npm run build`).
