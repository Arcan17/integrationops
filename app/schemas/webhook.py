"""Webhook schemas."""

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.models.enums import DeliveryStatus


class WebhookCreate(BaseModel):
    """Payload to register a webhook endpoint."""

    url: AnyHttpUrl
    event_types: list[str] = Field(default_factory=list, max_length=20)
    secret: str | None = Field(default=None, min_length=16, max_length=255)


class WebhookRead(BaseModel):
    """Webhook endpoint representation. The secret is returned once on creation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    event_types: list[str]
    is_active: bool
    secret: str
    created_at: datetime


class WebhookDeliveryRead(BaseModel):
    """A recorded webhook delivery attempt."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint_id: int
    event_type: str
    status: DeliveryStatus
    response_status: int | None
    attempts: int
    created_at: datetime
