# Contributing to Cap

Thank you for your interest in contributing. This document describes how to
work on the codebase safely and consistently.

## Code of Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By
contributing, you agree to uphold those standards.

## Project layout

```text
.
├── shared/                     # Shared value-object primitives
├── wallet_service/             # Trader balances & holdings
├── order_service/              # Order ingress (OIS)
├── matching_engine/            # In-memory matching (worker)
├── admin_service/              # Instruments & share allocation
├── market_data_service/        # Order book / LTP reads
├── balance_history_service/    # Event consumer → history store
├── notification_dispatcher/    # Event consumer → push to NS
├── notification_service/       # WebSocket + internal push API
├── docs/                       # Architecture & domain model
├── ADRs.md                     # Architecture Decision Records
├── ENDPOINTS.md                # HTTP / WebSocket contract
└── run_tests.sh                # Official test runner
```

Each service follows **hexagonal / clean architecture**:

```text
src/
├── domain/          # Entities, VOs, ports, domain events
├── application/     # Use-case handlers (commands / queries)
├── infrastructure/  # SQLAlchemy, RabbitMQ, Redis, HTTP clients
├── presentation/    # FastAPI routers & schemas (where applicable)
├── conf.py
└── app.py | worker.py
```

## Development setup

### Prerequisites

- Python 3.12+
- Optional for full stack: RabbitMQ, Redis, PostgreSQL

### Dependencies (mandatory)

Each service owns its dependencies in **`<service>/requirements.txt`**.

```bash
python -m pip install -r order_service/requirements.txt
```

Do **not** invent a global dependency set. If a package is needed, add it to that
service’s `requirements.txt` and use `run_tests.sh` so CI installs the same file.

### Tests (mandatory entrypoint)

From the **repository root**, always run:

```bash
sh run_tests.sh <service_directory>/ test/
```

Examples:

```bash
sh run_tests.sh order_service/ test/
sh run_tests.sh wallet_service/ test/
sh run_tests.sh matching_engine/ test/
```

`run_tests.sh` will:

1. Refuse to run if `<service>/requirements.txt` is missing
2. `pip install -r <service>/requirements.txt`
3. Execute pytest with `--confcutdir=<service>` so conftest isolation holds

Pull requests that document or rely on ad-hoc `python -m pytest ...` without
`run_tests.sh` should be updated to the official command.

Integrations (Wallet, Admin, RabbitMQ, Redis) default to **off** so unit and e2e
tests run without external infrastructure.

### Local run (single service example)

```bash
python -m pip install -r order_service/requirements.txt
export PYTHONPATH=.
export APP_ENV=development
export RABBITMQ_ENABLED=false
export WALLET_INTEGRATION_ENABLED=false
export ADMIN_INTEGRATION_ENABLED=false
uvicorn order_service.src.app:app --reload --port 8003
```

## Coding standards

Align with the project standards (see also repository `AGENTS.md` / Cap standards):

| Rule | Requirement |
|------|-------------|
| Style | PEP 8 |
| Types | Modern annotations (`list[str]`, `X \| None`) on public APIs |
| Docstrings | Google-style on public modules, classes, functions, methods |
| Comments | Only for non-obvious rationale (domain rules, security, perf) — not narration |
| Design | Prefer SRP, composition, early returns, expressive names |

### Architecture rules

1. **Domain** must not import infrastructure or presentation.
2. **Application** depends on domain ports only; adapters live in infrastructure.
3. **Publish domain events after successful commit** (not inside an open transaction).
4. **Consumers** (BHS, ND, ME worker, OIS fill worker, wallet settlement) are not public HTTP APIs.
5. Do not introduce VOs on the Matching Engine hot path without an explicit performance review.

### Git workflow

1. Branch from `main` (or the agreed default branch): `feature/<short-name>` or `fix/<issue-id>`.
2. Keep commits focused; prefer one logical change per commit.
3. Open a pull request with:
   - What changed and why
   - Tests run (exact `sh run_tests.sh …` command)
   - Any ADR impact (update [ADRs.md](ADRs.md) if a durable decision is made)
4. Ensure tests relevant to the touched service pass via `run_tests.sh`.

### Pull request checklist

- [ ] Code follows PEP 8 and Google-style docstrings on new public APIs
- [ ] No domain → infrastructure imports
- [ ] Unit and/or e2e tests updated for behavior changes
- [ ] Tests run via `sh run_tests.sh <service>/ test/` (not ad-hoc pytest)
- [ ] New runtime deps added to that service’s `requirements.txt`
- [ ] `ENDPOINTS.md` updated if HTTP contracts changed
- [ ] ADR added/updated for non-trivial architectural decisions
- [ ] No secrets, credentials, or private keys committed

## Reporting issues

Include:

- Service name and approximate version / commit
- Steps to reproduce
- Expected vs actual behavior
- Logs (redact secrets)

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).