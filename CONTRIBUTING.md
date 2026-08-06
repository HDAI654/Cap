# Contributing to Cap

Thank you for contributing. Follow this guide so changes stay consistent with
the existing microservices and coding standards.

## Code of Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) when present.

## Project layout

```text
.
├── shared/                      # Shared VO / entity primitives
├── auth_service/                # Identity, sessions, tokens, auth events
├── wallet_service/
├── order_service/
├── matching_engine/
├── admin_service/
├── market_data_service/
├── balance_history_service/     # Consumer only
├── notification_dispatcher/     # Consumer only
├── notification_service/
├── docs/
├── ADRs.md
└── run_tests.sh
```

Each service uses hexagonal layers: `domain` → `application` → `infrastructure` /
`presentation` (or `worker.py` for pure consumers).

## Dependencies (mandatory)

Each service owns **`<service>/requirements.txt`**.

```bash
python -m pip install -r auth_service/requirements.txt
python -m pip install -r gateway/requirements.txt
```

Do not invent a global dependency set. Add packages only to the service that needs them.

## Tests (mandatory entrypoint)

From the **repository root**:

```bash
sh run_tests.sh <service_directory>/ test/
```

Examples:

```bash
sh run_tests.sh auth_service/ test/
sh run_tests.sh order_service/ test/
```

`run_tests.sh` installs that service’s `requirements.txt`, sets `PYTHONPATH`, and
runs pytest with `--confcutdir=<service>`.

## Local run (examples)

**Auth**

```bash
python -m pip install -r auth_service/requirements.txt
export PYTHONPATH=.
export APP_ENV=development
export RABBITMQ_ENABLED=false
export REDIS_ENABLED=false
uvicorn auth_service.src.app:app --reload --port 8000
```

Integrations (Redis, RabbitMQ, Wallet/Admin HTTP) default **off** so unit and e2e
tests run without external infrastructure.

## Coding standards

| Rule | Requirement |
|------|-------------|
| Style | PEP 8 |
| Types | Modern annotations on public APIs |
| Docstrings | Google-style on public modules/classes/functions |
| Comments | Non-obvious rationale only (domain, security, perf) |
| Design | SRP, composition, early returns |

### Architecture rules

1. Domain must not import infrastructure or presentation.
2. Application depends on domain ports only.
3. Publish domain events **after** successful commit.
4. Consumers (BHS, ND, ME worker, …) are not public HTTP APIs.
5. Auth does **not** send email; it publishes `VerificationTokenCreated`.
6. Edge JWT / role checks will live in the planned API Gateway; until then, services may verify tokens at their boundary where required.

### Pull request checklist

- [ ] PEP 8 + Google-style docstrings on new public APIs
- [ ] No domain → infrastructure imports
- [ ] Tests updated; run via `sh run_tests.sh <service>/ test/`
- [ ] New deps in that service’s `requirements.txt`
- [ ] `ENDPOINTS.md` / docs updated if HTTP contracts changed
- [ ] ADR updated for durable architectural decisions
- [ ] No secrets committed

## License

Contributions are licensed under the [MIT License](LICENSE).
