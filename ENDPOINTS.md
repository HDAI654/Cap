# HTTP & WebSocket API Reference

Base paths are **per service**. Until an API Gateway is deployed, call each
service host directly. Path parameters that are IDs are **UUID v4** strings
(36 characters) unless noted otherwise.

Error body (typical):

```json
{ "detail": "Human-readable message" }
```

---

## Table of contents

1. [Wallet Service](#1-wallet-service)
2. [Order Service (OIS)](#2-order-service-ois)
3. [Admin Service](#3-admin-service)
4. [Market Data Service](#4-market-data-service)
5. [Notification Service](#5-notification-service)
6. [Services without public HTTP](#6-services-without-public-http)

---

## 1. Wallet Service

**Router prefix:** `/api/v1/wallets`

### 1.1 Create wallet

| | |
|--|--|
| **Method / URL** | `POST /api/v1/wallets` |
| **Success** | `201 Created` |

**Request body**

| Field | Type | Rules |
|-------|------|--------|
| `trader_id` | string | UUID, required |

```json
{ "trader_id": "11111111-1111-4111-8111-111111111111" }
```

**Response `201`**

```json
{ "wallet_id": "22222222-2222-4222-8222-222222222222" }
```

| Status | When |
|--------|------|
| 409 | Wallet already exists for trader |
| 422 | Invalid trader id |
| 503 | Database unavailable |

---

### 1.2 Get wallet by trader

| | |
|--|--|
| **Method / URL** | `GET /api/v1/wallets/by-trader/{trader_id}` |
| **Success** | `200 OK` |

**Response `200`** — same shape as [Get wallet](#13-get-wallet).

| Status | When |
|--------|------|
| 404 | No wallet for trader |

---

### 1.3 Get wallet

| | |
|--|--|
| **Method / URL** | `GET /api/v1/wallets/{wallet_id}` |
| **Success** | `200 OK` |

**Response `200`**

```json
{
  "wallet_id": "…",
  "trader_id": "…",
  "status": "ACTIVE",
  "cash_balances": [
    { "currency": "USD", "available": "1000.00", "reserved": "0.00" }
  ],
  "holdings": [
    {
      "instrument_id": "…",
      "available": 100,
      "reserved": 0,
      "average_cost": "10.50",
      "average_cost_currency": "USD"
    }
  ]
}
```

| Status | When |
|--------|------|
| 404 | Wallet not found |
| 422 | Invalid wallet id |

---

### 1.4 Lifecycle: lock / activate / close

| Method / URL | Success | Summary |
|--------------|---------|---------|
| `POST /api/v1/wallets/{wallet_id}/lock` | `204` | Lock wallet |
| `POST /api/v1/wallets/{wallet_id}/activate` | `204` | Activate wallet |
| `POST /api/v1/wallets/{wallet_id}/close` | `204` | Close wallet |

**Body:** none.

| Status | When |
|--------|------|
| 404 | Wallet not found |
| 409 / 422 | Invalid state transition |

---

### 1.5 Cash: deposit / withdraw

| Method / URL | Body | Success |
|--------------|------|---------|
| `POST /api/v1/wallets/{wallet_id}/deposits` | Money | `204` |
| `POST /api/v1/wallets/{wallet_id}/withdrawals` | Money | `204` |

**Money body**

```json
{ "amount": "100.00", "currency": "USD" }
```

| Field | Type | Rules |
|-------|------|--------|
| `amount` | decimal string | `> 0`, max 18 digits, 2 dp |
| `currency` | string | 3-letter code |

---

### 1.6 Cash: reserve / release / settle (consume)

| Method / URL | Body | Success | Purpose |
|--------------|------|---------|---------|
| `POST …/cash-reservations` | Money | `204` | Reserve available → reserved |
| `POST …/cash-releases` | Money | `204` | Release reserved → available |
| `POST …/cash-settlements` | Money | `204` | Consume reserved (settlement) |

---

### 1.7 Holdings: add / remove

**Add** — `POST /api/v1/wallets/{wallet_id}/holdings` → `204`

```json
{
  "instrument_id": "…",
  "quantity": 100,
  "average_cost": "10.50",
  "average_cost_currency": "USD"
}
```

**Remove** — `POST /api/v1/wallets/{wallet_id}/holding-removals` → `204`

```json
{ "instrument_id": "…", "quantity": 10 }
```

---

### 1.8 Holdings: reserve / release / settle

| Method / URL | Body | Success |
|--------------|------|---------|
| `POST …/holding-reservations` | HoldingQuantity | `204` |
| `POST …/holding-releases` | HoldingQuantity | `204` |
| `POST …/holding-settlements` | HoldingQuantity | `204` |

```json
{ "instrument_id": "…", "quantity": 10 }
```

---

## 2. Order Service (OIS)

**Router prefix:** `/api/v1/orders`

Submit **auto-opens** the order (`NEW` → `OPEN`) and publishes `OrderSubmitted`
and `OrderOpened` when the bus is enabled.

### 2.1 Submit order

| | |
|--|--|
| **Method / URL** | `POST /api/v1/orders` |
| **Success** | `201 Created` |

**Request body**

| Field | Type | Rules |
|-------|------|--------|
| `trader_id` | string | UUID |
| `instrument_id` | string | UUID |
| `side` | string | e.g. `BUY`, `SELL` |
| `order_type` | string | `LIMIT`, `MARKET` |
| `time_in_force` | string | e.g. `GTC`, `IOC` |
| `quantity` | int | `> 0` |
| `idempotency_key` | string | 1–128 chars |
| `limit_price` | decimal \| null | Required semantics for LIMIT; forbidden for MARKET |
| `limit_price_currency` | string \| null | 3-letter code when price set |

```json
{
  "trader_id": "…",
  "instrument_id": "…",
  "side": "BUY",
  "order_type": "LIMIT",
  "time_in_force": "GTC",
  "quantity": 100,
  "idempotency_key": "client-key-001",
  "limit_price": "10.50",
  "limit_price_currency": "USD"
}
```

**Response `201`**

```json
{ "order_id": "…" }
```

| Status | When |
|--------|------|
| 409 | Duplicate idempotency key; insufficient funds/holdings (if Wallet on) |
| 422 | Invalid params; instrument not tradable (if Admin on) |
| 503 | DB / wallet integration failure |

---

### 2.2 Get order

| | |
|--|--|
| **Method / URL** | `GET /api/v1/orders/{order_id}` |
| **Success** | `200 OK` |

**Response `200`**

```json
{
  "order_id": "…",
  "trader_id": "…",
  "instrument_id": "…",
  "side": "BUY",
  "order_type": "LIMIT",
  "time_in_force": "GTC",
  "quantity": 100,
  "filled_quantity": 0,
  "remaining_quantity": 100,
  "limit_price": "10.50",
  "limit_price_currency": "USD",
  "status": "OPEN",
  "idempotency_key": "client-key-001",
  "created_at": "2026-08-03T12:00:00+00:00",
  "updated_at": "2026-08-03T12:00:00+00:00"
}
```

| Status | When |
|--------|------|
| 404 | Order not found |

---

### 2.3 List orders by trader

| | |
|--|--|
| **Method / URL** | `GET /api/v1/orders?trader_id={uuid}` |
| **Success** | `200 OK` |

**Response `200`:** `OrderResponse[]` (same object as get).

---

### 2.4 Lifecycle actions

| Method / URL | Body | Success | Notes |
|--------------|------|---------|--------|
| `POST /api/v1/orders/{order_id}/open` | — | `204` | Conflict if already OPEN |
| `POST /api/v1/orders/{order_id}/fills` | `{ "fill_quantity": n }` | `204` | Partial/full fill |
| `POST /api/v1/orders/{order_id}/cancel` | — | `204` | Releases remaining reservation when Wallet on |
| `POST /api/v1/orders/{order_id}/reject` | — | `204` | **NEW only** (rare after auto-open) |
| `POST /api/v1/orders/{order_id}/expire` | — | `204` | OPEN / PARTIALLY_FILLED |

| Status | When |
|--------|------|
| 404 | Order not found |
| 409 | Illegal state transition |
| 422 | Invalid fill quantity / ids |

---

## 3. Admin Service

**Router prefix:** `/api/v1/instruments`  
**Auth:** `Authorization: Bearer <JWT>` — RS256 verify with `AUTH_PUBLIC_KEY`;
claim `role` must be `"ADMIN"`.

### 3.1 Create instrument

| | |
|--|--|
| **Method / URL** | `POST /api/v1/instruments` |
| **Success** | `201 Created` |

**Request body**

```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "tick_size": "0.01",
  "lot_size": 1,
  "minimum_order_quantity": 1,
  "maximum_order_quantity": 10000,
  "currency": "USD",
  "total_shares": 0
}
```

**Response `201`:** `{ "instrument_id": "…" }`

| Status | When |
|--------|------|
| 401 / 403 | Missing/invalid token or role |
| 409 | Symbol already exists |
| 422 | Validation error |

---

### 3.2 List / get

| Method / URL | Success | Response |
|--------------|---------|----------|
| `GET /api/v1/instruments` | `200` | `InstrumentResponse[]` |
| `GET /api/v1/instruments/{instrument_id}` | `200` | `InstrumentResponse` |

**InstrumentResponse**

```json
{
  "instrument_id": "…",
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "tick_size": "0.01",
  "tick_size_currency": "USD",
  "lot_size": 1,
  "minimum_order_quantity": 1,
  "maximum_order_quantity": 10000,
  "currency": "USD",
  "total_shares": 0,
  "status": "PENDING",
  "created_at": "…",
  "updated_at": "…"
}
```

`status`: `PENDING` \| `ACTIVE` \| `HALTED` \| `DELISTED`

---

### 3.3 Lifecycle & allocation

| Method / URL | Body | Success |
|--------------|------|---------|
| `POST …/{id}/activate` | — | `204` |
| `POST …/{id}/halt` | — | `204` |
| `POST …/{id}/delist` | — | `204` |
| `POST …/{id}/allocations` | `{ "quantity": n }` | `204` |

| Status | When |
|--------|------|
| 404 | Instrument not found |
| 409 | Illegal status transition |
| 401 / 403 | Auth failure |

---

## 4. Market Data Service

**Router prefix:** `/api/v1/market-data`

Reads Redis keys written by the Matching Engine (`md:book:…`, `md:ltp:…`).

### 4.1 Health

| Method / URL | Success |
|--------------|---------|
| `GET /health` | `200` `{ "status": "ok", "service": "MarketDataService" }` |

### 4.2 Order book

| | |
|--|--|
| **Method / URL** | `GET /api/v1/market-data/{instrument_id}/order-book` |
| **Success** | `200 OK` |

```json
{
  "instrument_id": "…",
  "bids": [{ "price": "100.00", "quantity": 50 }],
  "asks": [{ "price": "100.50", "quantity": 30 }],
  "last_trade_price": "100.25",
  "last_trade_currency": "USD"
}
```

| Status | When |
|--------|------|
| 404 | No snapshot in cache |
| 422 | Invalid instrument id |
| 503 | Redis unavailable |

### 4.3 Last trade price

| | |
|--|--|
| **Method / URL** | `GET /api/v1/market-data/{instrument_id}/last-trade-price` |
| **Success** | `200 OK` |

```json
{
  "instrument_id": "…",
  "price": "100.25",
  "currency": "USD"
}
```

| Status | When |
|--------|------|
| 404 | No LTP in cache |

---

## 5. Notification Service

### 5.1 Health

| Method / URL | Success |
|--------------|---------|
| `GET /health` | `200` |

```json
{
  "status": "ok",
  "service": "NotificationService",
  "connected_traders": 0
}
```

### 5.2 WebSocket (trader channel)

| | |
|--|--|
| **URL** | `WS /ws/v1/notifications/{trader_id}` |
| **Auth** | Expected at Gateway (service trusts path `trader_id`) |

**Server → client message**

```json
{
  "event_type": "OrderFilled",
  "payload": { "order_id": "…", "…": "…" }
}
```

Client may send text pings; payload is ignored. Disconnect removes the socket
from the hub.

### 5.3 Internal push (Notification Dispatcher only)

| | |
|--|--|
| **Method / URL** | `POST /internal/v1/notifications` |
| **Success** | `202 Accepted` |

**Request**

```json
{
  "event_type": "OrderSubmitted",
  "recipient_trader_ids": ["…"],
  "payload": { "order_id": "…" }
}
```

**Response `202`**

```json
{ "delivered": 1 }
```

`delivered` is the number of successful WebSocket sends (0 if no connections).

| Status | When |
|--------|------|
| 422 | Empty `event_type` or `recipient_trader_ids` |

> Not intended for public Gateway exposure.

---

## 6. Services without public HTTP

| Service | Interface |
|---------|-----------|
| **matching_engine** | Worker: consumes `OrderOpened` / `OrderCancelled`; publishes trade events; writes Redis |
| **balance_history_service** | Worker: consumes order/trade events → DB projections |
| **notification_dispatcher** | Worker: consumes events → `POST` NS internal API |
| **order_service** fill worker | Worker: consumes `OrderFilled` → updates order aggregate |
| **wallet_service** settlement worker | Worker: consumes `TradeExecuted` → settles wallets |

---

## Suggested local ports (convention)

| Service | Port |
|---------|------|
| Wallet | 8001 |
| Admin | 8002 |
| Order (OIS) | 8003 |
| Market Data | 8004 |
| Notification | 8008 |

These are **conventions only**; bind addresses are chosen by the process
launcher (`uvicorn`, etc.).
