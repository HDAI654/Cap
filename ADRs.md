# Architecture Decision Records

This document records **durable architectural decisions** for Cap.
Format follows the spirit of [Michael Nygard’s ADR pattern](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):
context, decision, consequences. Status values: **Accepted** | **Superseded** | **Deprecated**.

---

## ADR-001: Microservices with explicit bounded contexts

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Context

A monolithic exchange couples order entry, matching, balances, and market data
into one deployable unit, making independent scaling and failure isolation hard.

### Decision

Split the system into services aligned with domain capabilities:

- Wallet, Order Ingress, Matching Engine, Admin, Market Data API
- Event consumers: Balance & History, Notification Dispatcher
- Real-time edge: Notification Service
- Planned: API Gateway, Auth

### Consequences

- Independent deploy and scale per workload (especially ME).
- Cross-service consistency requires events and explicit integration ports.
- Operational complexity (bus, cache, multiple processes) increases.

---

## ADR-002: Hexagonal / clean architecture per service

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Context

Framework and persistence choices change; domain rules must remain testable
without FastAPI or SQLAlchemy.

### Decision

Each service uses layers:

1. **Domain** — entities, value objects, domain events, ports  
2. **Application** — command/query handlers  
3. **Infrastructure** — SQLAlchemy, RabbitMQ, Redis, HTTP clients  
4. **Presentation** — FastAPI (only for services that expose HTTP)

Domain must not import infrastructure or presentation.

### Consequences

- High unit-test coverage of domain and application with mocks.
- Adapters can be swapped (NoOp publisher, in-memory cache) for tests.
- Slightly more boilerplate than a “framework-first” layout.

---

## ADR-003: Domain-Driven Design with value objects and aggregates

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Context

Trading invariants (order state machine, money, quantities, wallet reservations)
are easy to scatter across controllers if modeled as primitive bags.

### Decision

- Model **aggregates** (e.g. `Order`, `Wallet`, `Instrument`) with explicit
  transitions and change trackers for partial persistence.
- Use **value objects** for IDs, money, quantity, enums (side, type, TIF, status).
- Enforce invariants in the domain; application orchestrates ports.

### Consequences

- Safer mutations and clearer APIs.
- More types and factories; onboarding cost for contributors.

---

## ADR-004: Matching Engine uses simple types on the hot path

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

ME is latency-sensitive. Full VO validation on every match step adds overhead.
ME only consumes bus events produced by trusted services.

### Decision

- Prefer `str` / `int` / `Decimal` (or tick integers) inside the order book.
- Keep richer VOs in OIS, Wallet, and Admin where user input is untrusted.
- Use price-time priority with efficient level structures (e.g. sorted levels +
  FIFO queues).

### Consequences

- Lower per-match overhead.
- Contract discipline on event payloads is mandatory (trust but schema-check).

---

## ADR-005: Event-driven integration via RabbitMQ topic exchanges

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

Synchronous call chains between OIS, ME, Wallet, and notifications create
coupling and availability coupling.

### Decision

- Publish domain integration events to topic exchanges:
  - `order.events` — OrderSubmitted, OrderOpened, OrderCancelled, …
  - `trade.events` — TradeExecuted, OrderFilled, OrderPlaced, OrderRemoved
- Consumers: ME, BHS, ND, OIS fill worker, Wallet settlement worker.
- **Publish after successful commit** in the producing service.
- Feature-flag the bus (`RABBITMQ_ENABLED`, default `false`) for isolated tests.

### Consequences

- Loose coupling and natural fan-out.
- Eventual consistency; handlers must be idempotent where duplicates are possible
  (e.g. trade projection by `trade_id`).

---

## ADR-006: Market data via Redis cache written by ME, read by MDA (and later OIS)

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

Traders need current book depth and last trade price without querying the ME
process directly.

### Decision

- ME writes:
  - `md:book:{instrument_id}` — depth snapshot + optional embedded LTP  
  - `md:ltp:{instrument_id}` — last trade price JSON  
- Market Data API reads those keys over HTTP.
- OIS LTP validation at submit is **planned** (not yet wired).

### Consequences

- Fast read path independent of ME HTTP surface.
- Cache can lag or be empty; readers must handle 404 / missing keys.

---

## ADR-007: Balance & History and Notification Dispatcher are consumers only

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

Early drafts exposed REST on BHS. Architecture places BHS and ND under
**Event Consumers**, not Gateway-routed services.

### Decision

- **BHS**: no public HTTP API; worker only; projects trades and order history
  into its store (Wallet may later read shared store).
- **ND**: no public HTTP API; consumes events; pushes to Notification Service
  internal API.
- **NS**: WebSocket for traders + **internal** HTTP push endpoint for ND.

### Consequences

- Clearer security boundary (no public history API until designed).
- History queries for end users may go through Wallet or a future read API.

---

## ADR-008: Order submit auto-opens (NEW → OPEN) and emits OrderOpened

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

ME only matches on `OrderOpened`. Leaving orders in `NEW` until a separate
`POST .../open` meant nothing reached the book in the default flow.

### Decision

On successful submit (after instrument/wallet checks when enabled):

1. Persist order as NEW then transition to **OPEN** in the same unit of work.
2. Publish **OrderSubmitted** and **OrderOpened**.

Explicit `POST /orders/{id}/open` remains for edge/admin-style use; re-open of
already OPEN yields conflict.

### Consequences

- Matching works without an extra orchestration hop.
- `reject` (NEW-only) is largely unused for the happy path; cancel/expire apply
  to book-visible states.

---

## ADR-009: Cross-service Wallet and Admin integration via ports + HTTP adapters

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

OIS must not embed Wallet or Admin persistence; tests must run without those
services.

### Decision

- Define ports: `WalletGateway`, `InstrumentGateway`.
- Provide **HTTP** adapters and **NoOp** adapters.
- Gate with `WALLET_INTEGRATION_ENABLED` / `ADMIN_INTEGRATION_ENABLED`
  (default `false`).
- Wallet exposes `GET /api/v1/wallets/by-trader/{trader_id}` for resolution.
- Submit reserves (LIMIT buy notional / sell quantity); cancel releases remainder.
- Wallet **settlement worker** consumes `TradeExecuted` to consume reserved
  assets and credit counterparties.
- OIS **fill worker** consumes `OrderFilled` to update order aggregates.

### Consequences

- Correct end-to-end money path when flags and bus are enabled.
- Operational dependency on Wallet/Admin availability when flags are on.
- MARKET buy cash reserve still needs LTP (deferred).

---

## ADR-010: Admin authorization is JWT verify-only with role claim

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

Auth issuance is a separate future service. Admin mutations must still be
protected.

### Decision

- Admin Service decodes JWT with `AUTH_PUBLIC_KEY` (RS256).
- Require claim `role == "ADMIN"`.
- No login/refresh endpoints in Admin Service.

### Consequences

- Simple, aligned with split Auth service.
- Gateway or clients must obtain tokens elsewhere.

---

## ADR-011: Persistence with async SQLAlchemy 2.0 and fine-grained change tracking

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Context

Aggregates (wallet, order) update only subsets of related rows; full rewrite is
wasteful and racy.

### Decision

- Async SQLAlchemy 2.0 + unit of work per use case.
- Domain change trackers (created/updated/removed cash, holdings, status, fills)
  drive partial updates.
- Default test DB: SQLite in-memory; production URL via `DATABASE_URL`.

### Consequences

- Efficient updates; slightly more mapper/repository complexity.

---

## ADR-012: Testing strategy — pyramid with service-local conftest isolation

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Context

Multiple services share a monorepo; pytest collection collides without isolation.

### Decision

- Unit tests: domain, application (mocked ports), infrastructure (in-memory DB).
- E2E: FastAPI `TestClient` where the service has HTTP.
- **Official test entrypoint** from repository root:

   ```bash
   sh run_tests.sh <service_directory>/ test/
   ```

   Example: `sh run_tests.sh order_service/ test/`

### Consequences

- Reliable CI per service; full-stack bus tests remain optional/manual.

---

## ADR index

| ID | Title | Status |
|----|--------|--------|
| 001 | Microservices with bounded contexts | Accepted |
| 002 | Hexagonal architecture per service | Accepted |
| 003 | DDD aggregates and value objects | Accepted |
| 004 | ME simple types on hot path | Accepted |
| 005 | RabbitMQ topic event integration | Accepted |
| 006 | Redis market data cache contract | Accepted |
| 007 | BHS / ND consumers only | Accepted |
| 008 | Submit auto-opens orders | Accepted |
| 009 | Wallet/Admin ports + settlement/fill workers | Accepted |
| 010 | Admin JWT verify-only | Accepted |
| 011 | Async SQLAlchemy + change tracking | Accepted |
| 012 | Testing pyramid + confcutdir | Accepted |
