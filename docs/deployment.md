# Deployment Notes

IntegrationOps is container-ready. This document outlines what a production
deployment requires; it is intentionally platform-agnostic.

## Build

```bash
docker build -t integrationops:latest .
```

The same image runs both roles:
- **API:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Worker:** `celery -A app.workers.celery_app.celery_app worker`

For higher API throughput, run Uvicorn behind a process manager
(e.g. `uvicorn --workers N` or Gunicorn with Uvicorn workers).

## Required configuration

All configuration is environment-driven (see `.env.example`):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | **Required.** Strong random value (`openssl rand -hex 32`). |
| `DATABASE_URL` | Managed PostgreSQL connection string. |
| `REDIS_URL` | Managed Redis connection string. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime. |
| `MAX_UPLOAD_SIZE_BYTES` | Upload size guard. |
| `EXPORT_DIR` | Writable path (use a persistent volume or object storage). |

## Database migrations

Run migrations as a release step before starting new app instances:

```bash
alembic upgrade head
```

## Operational checklist

- [ ] `SECRET_KEY` set to a unique, strong value (never the dev default).
- [ ] PostgreSQL and Redis are managed services with backups/persistence.
- [ ] Migrations applied as part of the deploy pipeline.
- [ ] At least one API replica and one worker replica running.
- [ ] `EXPORT_DIR` backed by durable storage (volume or object storage).
- [ ] HTTPS terminated at the load balancer / ingress.
- [ ] Health check wired to `GET /api/v1/health`.
- [ ] Log aggregation in place for API and worker.

## Scaling

- **API** scales horizontally (stateless; JWT auth).
- **Worker** scales by adding replicas; Redis coordinates the queue.
- **Retries** are bounded per job (`max_attempts`); failed jobs are
  inspectable and re-runnable via `POST /jobs/{id}/retry`.

## Security posture

- No secrets in code; typed settings + `.env`.
- Passwords hashed with bcrypt; auth via short-lived JWTs.
- RBAC enforced at the dependency layer (`admin` / `operator` / `viewer`).
- Uploads constrained by extension and size; filenames sanitized against
  path traversal; files processed in memory.
- Webhooks signed with HMAC-SHA256 so receivers can verify authenticity.
