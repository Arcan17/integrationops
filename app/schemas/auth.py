"""Authentication-related schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2-style bearer token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT claims relevant to the application."""

    sub: str | None = None
