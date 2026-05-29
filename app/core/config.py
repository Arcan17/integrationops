"""Typed application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central, typed configuration for the IntegrationOps backend.

    Values are read from environment variables (or a local ``.env`` file).
    No secrets are hardcoded; see ``.env.example`` for the expected keys.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    PROJECT_NAME: str = "IntegrationOps"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # Infrastructure connection strings (used in later phases)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://integrationops:integrationops@db:5432/integrationops"
    )
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # Security / JWT
    # NOTE: override SECRET_KEY in every non-local environment via the .env file.
    SECRET_KEY: str = Field(default="dev-insecure-secret-change-me")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # File ingestion limits
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=5 * 1024 * 1024)  # 5 MB
    ALLOWED_UPLOAD_EXTENSIONS: tuple[str, ...] = (".csv", ".xlsx")

    # Celery / async processing
    # Broker and result backend default to REDIS_URL; override if separated.
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)
    JOB_RETRY_COUNTDOWN_SECONDS: int = Field(default=5)

    # Exports & webhooks
    EXPORT_DIR: str = Field(default="exports")
    WEBHOOK_TIMEOUT_SECONDS: float = Field(default=10.0)

    # CORS — origins allowed to call the API (e.g. the local dashboard)
    CORS_ORIGINS: tuple[str, ...] = ("http://localhost:3000",)

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
