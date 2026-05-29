"""Unit tests for the row validation engine."""

from app.services.validation import validate_row


def _row(**overrides) -> dict[str, str]:
    base = {
        "external_id": "C-1",
        "email": "User@Example.com",
        "amount": "10.50",
        "signup_date": "2026-01-15",
        "status": "active",
    }
    base.update(overrides)
    return base


def test_valid_row_is_normalized():
    result = validate_row(_row(), row_number=1)
    assert result.is_valid
    assert result.cleaned["email"] == "user@example.com"
    assert result.cleaned["amount"] == 10.5
    assert result.cleaned["signup_date"] == "2026-01-15"


def test_missing_required_field():
    result = validate_row(_row(external_id=""), row_number=2)
    assert not result.is_valid
    assert result.errors[0]["error_code"] == "required_missing"


def test_invalid_email_number_and_choice():
    result = validate_row(
        _row(email="not-an-email", amount="abc", status="unknown"), row_number=3
    )
    codes = {e["error_code"] for e in result.errors}
    assert codes == {"invalid_email", "invalid_number", "invalid_choice"}


def test_below_minimum_and_invalid_date():
    result = validate_row(_row(amount="-1", signup_date="15-01-2026"), row_number=4)
    codes = {e["error_code"] for e in result.errors}
    assert "below_minimum" in codes
    assert "invalid_date" in codes


def test_optional_fields_can_be_blank():
    result = validate_row(_row(signup_date="", status=""), row_number=5)
    assert result.is_valid
    assert "signup_date" not in result.cleaned
