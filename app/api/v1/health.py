"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = "ok"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns the service status. Used by orchestrators and uptime checks.",
)
def health() -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse()
