"""Shared pytest fixtures.

Unit tests run with no external services. Integration tests need a reachable
PostgreSQL database (configured via ``DATABASE_URL``); when it is unavailable
they are skipped automatically. Celery runs in eager mode so jobs execute
synchronously in-process.
"""

import os

# Configure the environment before importing application modules.
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JOB_RETRY_COUNTDOWN_SECONDS", "0")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import Base
from app.models.enums import UserRole
from app.services.user import create_user
from app.schemas.user import UserCreate

get_settings.cache_clear()


@pytest.fixture(scope="session")
def db_engine():
    """Create the schema on a reachable test database, or skip if unavailable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("PostgreSQL is not reachable; skipping integration tests")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db(db_engine):
    """Provide a clean session, truncating all tables before each test."""
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db) -> TestClient:
    """A TestClient bound to the app with a clean database."""
    return TestClient(app)


def make_user(db, email: str, password: str, role: UserRole) -> int:
    """Create a user with a specific role and return its id."""
    user = create_user(
        db, UserCreate(email=email, password=password, full_name=None), role=role
    )
    return user.id


def auth_header(client: TestClient, email: str, password: str) -> dict[str, str]:
    """Log in via the API and return an Authorization header."""
    resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
