.PHONY: up down build logs migrate revision create-admin test fmt

# Start the full stack (api, worker, postgres, redis).
up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f api worker

# Apply database migrations inside the api container.
migrate:
	docker compose run --rm api alembic upgrade head

# Autogenerate a new migration: make revision m="add table"
revision:
	docker compose run --rm api alembic revision --autogenerate -m "$(m)"

# Create an initial admin user: make create-admin email=a@b.com password=secret123
create-admin:
	docker compose run --rm api python scripts/create_admin.py --email "$(email)" --password "$(password)"

# Run the test suite locally (requires requirements-dev.txt installed).
test:
	pytest
