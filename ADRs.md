# Architecture Decision Records

Durable decisions for Cap. Format: context → decision → consequences.

---

## ADR-001: Microservices with explicit bounded contexts

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Decision

Split the exchange into services: Auth, Wallet, Order Ingress, Matching
Engine, Admin, Market Data, Balance & History, Notification Dispatcher,
Notification Service. API Gateway is planned as a separate edge component.

### Consequences

Independent deploy/scale; cross-service consistency via events and ports.

---

## ADR-002: Hexagonal / clean architecture per service

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Decision

Layers: domain (entities, VOs, ports, events) → application (handlers) →
infrastructure (adapters) → presentation or worker entrypoint.

Domain must not import infrastructure or presentation.

---

## ADR-003: Domain-Driven Design with aggregates and value objects

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Decision

Model aggregates with explicit transitions; use VOs for IDs, money, quantities,
roles, tokens. Enforce invariants in domain.

---

## ADR-004: Matching Engine uses simple types on the hot path

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

Prefer simple types inside the ME order book; richer VOs remain in OIS/Wallet/Admin.

---

## ADR-005: Event-driven integration via RabbitMQ topic exchanges

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

Publish integration events after successful commit. Feature-flag the bus
(`RABBITMQ_ENABLED`, default false) for isolated tests.

Exchanges include order/trade events and **auth.events** (e.g. login, register,
`VerificationTokenCreated`).

---

## ADR-006: Market data via Redis cache (ME writes, MDA reads)

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

ME writes `md:book:*` / `md:ltp:*`; Market Data API reads them. OIS LTP validation
at submit remains planned.

---

## ADR-007: Balance & History and Notification Dispatcher are consumers only

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

No public HTTP for BHS/ND. NS exposes WebSocket + internal push API.

---

## ADR-008: Order submit auto-opens (NEW → OPEN) and emits OrderOpened

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

Successful submit persists, opens, and publishes `OrderSubmitted` + `OrderOpened`
so ME can match without a separate open hop.

---

## ADR-009: Cross-service Wallet and Admin integration via ports + HTTP adapters

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

OIS uses `WalletGateway` / `InstrumentGateway` with HTTP and NoOp adapters;
feature flags default off.

---

## ADR-010: Admin authorization is JWT verify-only with role claim

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

Admin Service verifies JWT with `AUTH_PUBLIC_KEY` and requires `role == "ADMIN"`.
Token issuance is owned by Auth Service.

---

## ADR-011: Persistence with async SQLAlchemy 2.0 and change tracking

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-07 |

### Decision

Async SQLAlchemy 2.0, unit of work per use case, fine-grained change trackers
where aggregates update subsets of rows. Default test DB: SQLite in-memory.

---

## ADR-012: Testing strategy — run_tests.sh + per-service requirements.txt

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Decision

Official test entrypoint:

```bash
sh run_tests.sh <service_directory>/ test/
```

Each service ships `requirements.txt`. Runner installs it and uses
`--confcutdir=<service>`.

---

## ADR-013: Dedicated Auth Service (sessions, tokens, auth events)

| Field | Value |
|-------|--------|
| **Status** | Accepted |
| **Date** | 2026-08 |

### Context

Identity and session lifecycle must not be embedded in trading services. Email
delivery is event-driven, not inline in Auth.

### Decision

- **auth_service** owns signup, login, admin login, logout, password flows,
  session lifecycle, and RS256 access/refresh tokens.
- Users persist in SQL; **sessions and verification tokens persist in Redis**
  when `REDIS_ENABLED` (in-memory adapters for tests).
- Auth publishes domain events (`UserRegistered`, `UserLoggedIn`,
  `UserLoggedOut`, `AccountDeleted`, **`VerificationTokenCreated`**).
- Auth **does not send email**; notification pipeline consumes
  `VerificationTokenCreated` (`token_type`: `verifyemail` |
  `forget_pass_verify`).
- Password strength rules apply on write paths only; login verifies hash only.
- Elevated admin login requires account password **and** `ADMIN_PASSWORD_HASH`.

### Consequences

Clear identity boundary; trading services trust JWT claims; email is decoupled
via the bus.

---

## ADR-014: API Gateway — edge authZ and reverse proxy

| Field | Value |
|-------|--------|
| **Status** | Proposed (not implemented) |
| **Date** | 2026-08 |

### Context

Clients should not call every microservice directly. Auth routes must remain
reachable without a prior token.

### Decision (target)

- Edge component verifies JWT locally with `AUTH_PUBLIC_KEY`.
- Route policy (intended):
  - `/api/v1/auth/*` — public (Auth enforces its own rules)
  - `/api/v1/orders|wallets|market-data/*` — authenticated (`USER` or `ADMIN`)
  - `/api/v1/instruments/*` — ADMIN only
  - `/ws/v1/notifications/{trader_id}` — JWT; USER only own id
- Forward identity headers upstream; do not expose internal push APIs.

### Consequences

Until implemented, clients call services directly; Admin continues local JWT
verify (ADR-010). This ADR records the intended edge design only.

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
| 009 | Wallet/Admin ports + workers | Accepted |
| 010 | Admin JWT verify-only | Accepted |
| 011 | Async SQLAlchemy + change tracking | Accepted |
| 012 | run_tests.sh + per-service requirements.txt | Accepted |
| 013 | Dedicated Auth Service | Accepted |
| 014 | API Gateway edge authZ + proxy | Proposed |
