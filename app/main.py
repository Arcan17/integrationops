"""FastAPI application entrypoint for IntegrationOps."""

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=__version__,
    description=(
        "IntegrationOps — a backend platform for data ingestion, validation, "
        "async processing, API automation and operational workflows."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"], summary="Service root")
def root() -> dict[str, str]:
    """Return basic service identification."""
    return {"service": settings.PROJECT_NAME, "version": __version__}
