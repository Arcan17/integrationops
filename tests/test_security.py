"""Unit tests for security helpers."""

import hashlib
import hmac

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.webhooks import sign_payload


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="42")
    claims = decode_access_token(token)
    assert claims["sub"] == "42"


def test_webhook_signature_matches_manual_hmac():
    secret = "a" * 32
    body = b'{"event_type":"x"}'
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert sign_payload(secret, body) == expected
