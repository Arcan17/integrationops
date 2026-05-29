# Local Setup

## Prerequisites

- Docker + Docker Compose, **or** Python 3.12 with local PostgreSQL and Redis.

## 1. Configure environment

```bash
cp .env.example .env
# Set a strong SECRET_KEY, e.g.:
#   openssl rand -hex 32
```

## 2. Start the stack (Docker)

```bash
docker compose up --build
# or: make up
```

Services:
- API → http://localhost:8000
- Swagger UI → http://localhost:8000/docs
- Health → http://localhost:8000/api/v1/health

## 3. Apply migrations

```bash
make migrate
# or: docker compose run --rm api alembic upgrade head
```

## 4. Create an initial admin

```bash
make create-admin email=admin@example.com password=secret123
# or: docker compose run --rm api python scripts/create_admin.py \
#       --email admin@example.com --password secret123
```

## 5. Walkthrough (curl)

```bash
BASE=http://localhost:8000/api/v1

# Login (admins can perform every operation)
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -d "username=admin@example.com&password=secret123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Upload a CSV
printf 'external_id,email,amount\nC-1,a@b.com,10\nC-2,c@d.com,5\n' > sample.csv
BATCH=$(curl -s -X POST "$BASE/uploads" -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.csv" | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Run a summarize job
curl -s -X POST "$BASE/jobs" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"batch_id\": $BATCH, \"job_type\": \"summarize\"}"

# Request a CSV export, then download it
curl -s -X POST "$BASE/exports" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"batch_id\": $BATCH, \"export_format\": \"csv\"}"
```

## Running without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://integrationops:integrationops@localhost:5432/integrationops
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head
uvicorn app.main:app --reload                       # API
celery -A app.workers.celery_app.celery_app worker  # Worker (separate shell)
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```
