# IntegrationOps

![CI](https://github.com/Arcan17/integrationops/actions/workflows/ci.yml/badge.svg)

A Python backend platform for **data ingestion, validation, async processing, API automation and operational workflows**.

IntegrationOps lets users upload messy business data (CSV/XLSX), validates and stores clean records in PostgreSQL, runs async processing jobs with retry support, tracks job status, exports results, emits webhook notifications, and records an operational audit trail — modeled as a realistic internal company platform.

## Features

- JWT authentication with role-based access control (`admin` / `operator` / `viewer`)
- CSV/XLSX upload with declarative, row-level validation and structured error reporting
- Clean records persisted to PostgreSQL; raw files processed in memory
- Async processing jobs (Celery + Redis) with status tracking and bounded retries
- Signed (HMAC-SHA256) webhook notifications with per-attempt delivery records
- CSV/XLSX exports of validated data
- Operational audit log for every significant action
- Dockerized stack, Alembic migrations, pytest suite and GitHub Actions CI

## Tech stack

| Area | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Async jobs | Celery + Redis |
| Packaging / runtime | Docker + Docker Compose |
| Testing & CI | pytest + GitHub Actions |
| API docs | OpenAPI (Swagger UI) |

## Architecture (target)

```
app/
  main.py            # FastAPI entrypoint
  core/config.py     # Typed settings (Pydantic)
  api/v1/            # Versioned API routers
  db/                # Session & base (Phase 2)
  models/            # SQLAlchemy models (Phase 2)
  schemas/           # Pydantic schemas
  services/          # Business logic (ingestion, validation, exports...)
  workers/           # Celery tasks (Phase 5)
tests/               # pytest suite (Phase 7)
docs/                # Architecture & operational docs (Phase 8)
```

## Run locally (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### Bootstrap an admin user

```bash
make create-admin email=admin@example.com password=secret123
```

A full curl walkthrough (upload → job → export) is in
[docs/local-setup.md](docs/local-setup.md).

## Run locally (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Database migrations (Alembic)

```bash
# Apply migrations (inside the api container or a local venv with DATABASE_URL set)
alembic upgrade head

# Create a new revision from model changes
alembic revision --autogenerate -m "describe change"
```

## Data validation

Uploaded rows are validated against a declarative schema in
`app/services/validation.py`. The default business-record schema:

| Column | Required | Rule |
|---|---|---|
| `external_id` | yes | non-empty, max 64 chars |
| `email` | yes | valid email (normalized to lowercase) |
| `amount` | yes | number ≥ 0 |
| `signup_date` | no | `YYYY-MM-DD` |
| `status` | no | one of `active`, `inactive` |

Valid rows are stored in `data_records`; failures are recorded in
`validation_errors` and exposed via `GET /api/v1/uploads/{id}/errors`.
Uploads are limited to `.csv` / `.xlsx` and `MAX_UPLOAD_SIZE_BYTES` (default 5 MB).

## Webhooks, exports & audit

- **Webhooks** — register endpoints subscribed to events (`upload.ingested`,
  `job.succeeded`, …). Deliveries run async via Celery and are signed with
  HMAC-SHA256 in the `X-IntegrationOps-Signature` header (verify with the
  endpoint secret).
- **Exports** — `POST /api/v1/exports` queues a CSV/XLSX export of a batch's
  clean records; poll `GET /api/v1/exports/{id}` and download via
  `GET /api/v1/exports/{id}/download`.
- **Audit logs** — every significant operation is recorded and queryable at
  `GET /api/v1/audit-logs` (admin only).

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

- **Unit tests** (validation, parsing, security, webhook signing) run with no
  external services.
- **Integration tests** (auth → upload → job → export) require a reachable
  PostgreSQL (`DATABASE_URL`) and run Celery in eager mode; they are skipped
  automatically when no database is available.

CI runs on GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)):
it spins up PostgreSQL + Redis, validates Alembic migrations (`upgrade` +
`downgrade`), and runs the full test suite.

## Roadmap

- [x] **Phase 1** — Backend skeleton (FastAPI, config, health, Docker Compose)
- [x] **Phase 2** — Database models & Alembic migrations
- [x] **Phase 3** — JWT authentication & role-based access control
- [x] **Phase 4** — CSV/XLSX ingestion & validation
- [x] **Phase 5** — Celery/Redis async jobs & retries
- [x] **Phase 6** — Webhooks, exports & audit logs
- [x] **Phase 7** — Tests & CI
- [x] **Phase 8** — Documentation & deploy readiness

## Documentation

- [Architecture](docs/architecture.md) — components, layers, data model, key flows
- [Local setup](docs/local-setup.md) — run the stack and a full API walkthrough
- [Deployment](docs/deployment.md) — production checklist and configuration
- [Screenshots](docs/screenshots.md) — what to capture for the portfolio
