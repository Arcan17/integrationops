"""Webhook endpoint management."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.webhook import WebhookEndpoint
from app.models.user import User
from app.schemas.webhook import WebhookCreate, WebhookRead
from app.services.webhooks import create_endpoint

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "",
    response_model=WebhookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a webhook endpoint",
    description="Registers a webhook. A signing secret is generated if none is provided.",
)
def register_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.operator)),
) -> WebhookEndpoint:
    """Register a webhook endpoint owned by the current user."""
    return create_endpoint(
        db,
        owner_id=current_user.id,
        url=str(payload.url),
        event_types=payload.event_types,
        secret=payload.secret,
    )


@router.get("", response_model=list[WebhookRead], summary="List webhook endpoints")
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WebhookEndpoint]:
    """List the caller's webhook endpoints (admins see all)."""
    stmt = select(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc())
    if current_user.role is not UserRole.admin:
        stmt = stmt.where(WebhookEndpoint.owner_id == current_user.id)
    return list(db.scalars(stmt))
