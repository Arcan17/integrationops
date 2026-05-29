"""Webhook registration, event emission and signed delivery."""

import hashlib
import hmac
import json
import secrets
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import DeliveryStatus
from app.models.webhook import WebhookDelivery, WebhookEndpoint

settings = get_settings()

SIGNATURE_HEADER = "X-IntegrationOps-Signature"


def generate_secret() -> str:
    """Return a new random webhook signing secret."""
    return secrets.token_hex(32)


def sign_payload(secret: str, body: bytes) -> str:
    """Return the hex HMAC-SHA256 signature for a payload body."""
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _matching_endpoints(db: Session, event_type: str) -> list[WebhookEndpoint]:
    """Return active endpoints subscribed to the event (empty list = all events)."""
    endpoints = db.scalars(
        select(WebhookEndpoint).where(WebhookEndpoint.is_active.is_(True))
    )
    return [ep for ep in endpoints if not ep.event_types or event_type in ep.event_types]


def emit_event(db: Session, event_type: str, payload: dict[str, Any]) -> list[int]:
    """Create pending deliveries for matching endpoints and dispatch them.

    Returns the list of created delivery ids.
    """
    body = {"event_type": event_type, "data": payload}
    deliveries = [
        WebhookDelivery(
            endpoint_id=ep.id,
            event_type=event_type,
            payload=body,
            status=DeliveryStatus.pending,
        )
        for ep in _matching_endpoints(db, event_type)
    ]
    if not deliveries:
        return []

    db.add_all(deliveries)
    db.commit()

    # Lazy import to avoid a circular import with the Celery tasks module.
    from app.workers.tasks import deliver_webhook

    ids = [d.id for d in deliveries]
    for delivery_id in ids:
        deliver_webhook.delay(delivery_id)
    return ids


def send_delivery(db: Session, delivery_id: int) -> None:
    """Perform the signed HTTP POST for a single delivery and record the outcome."""
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        return
    endpoint = db.get(WebhookEndpoint, delivery.endpoint_id)
    if endpoint is None:
        return

    body = json.dumps(delivery.payload, default=str).encode()
    headers = {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: sign_payload(endpoint.secret, body),
        "X-IntegrationOps-Event": delivery.event_type,
    }

    delivery.attempts += 1
    try:
        response = httpx.post(
            endpoint.url,
            content=body,
            headers=headers,
            timeout=settings.WEBHOOK_TIMEOUT_SECONDS,
        )
        delivery.response_status = response.status_code
        delivery.status = (
            DeliveryStatus.delivered
            if 200 <= response.status_code < 300
            else DeliveryStatus.failed
        )
    except httpx.HTTPError:
        delivery.status = DeliveryStatus.failed
    db.commit()


def create_endpoint(
    db: Session,
    *,
    owner_id: int,
    url: str,
    event_types: list[str],
    secret: str | None = None,
) -> WebhookEndpoint:
    """Register a new webhook endpoint, generating a secret when none is given."""
    endpoint = WebhookEndpoint(
        owner_id=owner_id,
        url=url,
        secret=secret or generate_secret(),
        event_types=event_types,
        is_active=True,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint
