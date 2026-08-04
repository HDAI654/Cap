# Cap - Stock Exchange (🚧 In Development)

![Status](https://img.shields.io/badge/status-active--development-yellow)
![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)

A scalable, event-driven stock exchange platform built with **microservices**,
**Domain-Driven Design (DDD)**, and **hexagonal architecture**.



### Services

| Service | Role | Entry |
|---------|------|--------|
| **wallet_service** | Cash & holdings lifecycle | HTTP API |
| **order_service** | Order ingress, lifecycle, fill apply | HTTP API + fill worker |
| **matching_engine** | In-memory price-time priority book | Worker |
| **admin_service** | Instruments & share allocation (ADMIN JWT) | HTTP API |
| **market_data_service** | Read order book / last trade price | HTTP API |
| **balance_history_service** | Project trades & order history | Consumer worker |
| **notification_dispatcher** | Route events → NS | Consumer worker |
| **notification_service** | WebSocket fan-out + internal push | HTTP + WebSocket |

See [docs/high-level-architecture.md](docs/high-level-architecture.md) and
[ADRs.md](ADRs.md) for design rationale.

## Documentation

| Document | Description |
|----------|-------------|
| [ENDPOINTS.md](ENDPOINTS.md) | Full HTTP / WebSocket contracts |
| [ADRs.md](ADRs.md) | Architecture Decision Records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [LICENSE](LICENSE) | MIT |
| [docs/](docs/) | Domain model & architecture diagrams |

## Quick start

### Prerequisites

- Python **3.12+**
- Optional: RabbitMQ, Redis, PostgreSQL (integrations off by default)

### Install & test a service (required workflow)

Dependencies are **per service**. Do not install ad-hoc packages from the
README list — use that service’s `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate

# From repository root — installs <service>/requirements.txt then runs tests
sh run_tests.sh order_service/ test/
sh run_tests.sh wallet_service/ test/
```

**Official test command**

```bash
sh run_tests.sh <service_directory>/ test/
```

Examples: `order_service/`, `wallet_service/`, `admin_service/`,
`matching_engine/`, `market_data_service/`, `balance_history_service/`,
`notification_dispatcher/`, `notification_service/`.

### Run an API (example: Order Service)

```bash
python -m pip install -r order_service/requirements.txt
export PYTHONPATH=.
export APP_ENV=development
export RABBITMQ_ENABLED=false
export WALLET_INTEGRATION_ENABLED=false
export ADMIN_INTEGRATION_ENABLED=false
uvicorn order_service.src.app:app --reload --port 8003
# OpenAPI: http://127.0.0.1:8003/docs
```

### Feature flags (typical)

| Variable | Default | Meaning |
|----------|---------|---------|
| `RABBITMQ_ENABLED` | `false` | Publish/consume on the bus |
| `REDIS_ENABLED` | `false` | ME writes / MDA reads cache |
| `WALLET_INTEGRATION_ENABLED` | `false` | OIS calls Wallet on submit/cancel |
| `ADMIN_INTEGRATION_ENABLED` | `false` | OIS checks instrument ACTIVE |
| `DATABASE_URL` | in-memory SQLite | Async SQLAlchemy URL |

## Core trading flow (when integrations are on)

1. **Admin** creates instrument → activates → (operators fund wallets / holdings).
2. **Trader** submits order via OIS → instrument check → wallet reserve → **auto OPEN** → `OrderSubmitted` + `OrderOpened`.
3. **Matching Engine** consumes `OrderOpened` → matches → publishes `TradeExecuted` / `OrderFilled` → updates Redis.
4. **OIS fill worker** applies `OrderFilled` to the order aggregate.
5. **Wallet settlement worker** settles `TradeExecuted` (consume reserved, credit counterparty).
6. **BHS** records history; **ND → NS** pushes real-time updates.

## Design principles

- **Bounded contexts** with explicit ports and adapters
- **Domain events** after successful persistence
- **Async** SQLAlchemy 2.0, FastAPI, aio-pika, redis.asyncio
- **Matching Engine** optimized for latency (simple types on the hot path)
- **Tests** per layer: domain / application / infrastructure / e2e

## Status & roadmap

**Implemented:** Wallet, OIS, ME, Admin, MDA, BHS, ND, NS, cross-service reserve/fill/settlement hooks.

**Planned / partial:**

- API Gateway & dedicated Auth service
- OIS last-trade-price validation from cache
- Unified shared history store for Wallet ↔ BHS
- Production deployment manifests

## License

[MIT](LICENSE) © 2026 Cap contributors.
