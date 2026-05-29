"""Declarative, row-level validation engine for ingested business data.

The default schema models a generic business record. Each row is validated
against the schema, producing a normalized payload plus a list of structured
errors that can be persisted to ``validation_errors``.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

_EMAIL_LOCAL_DOMAIN = 2  # parts expected when splitting on "@"


@dataclass(frozen=True)
class FieldSpec:
    """Validation specification for a single column."""

    name: str
    required: bool = False
    kind: str = "string"  # one of: string, email, number, date, enum
    choices: tuple[str, ...] = ()
    min_value: float | None = None
    max_length: int | None = None


# Default business-record schema. Adjust here to fit a concrete domain.
RECORD_SCHEMA: tuple[FieldSpec, ...] = (
    FieldSpec("external_id", required=True, kind="string", max_length=64),
    FieldSpec("email", required=True, kind="email"),
    FieldSpec("amount", required=True, kind="number", min_value=0),
    FieldSpec("signup_date", required=False, kind="date"),
    FieldSpec("status", required=False, kind="enum", choices=("active", "inactive")),
)


@dataclass
class RowResult:
    """Outcome of validating a single row."""

    cleaned: dict[str, Any]
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _is_valid_email(value: str) -> bool:
    parts = value.split("@")
    return len(parts) == _EMAIL_LOCAL_DOMAIN and all(parts) and "." in parts[1]


def _validate_field(spec: FieldSpec, raw: str) -> tuple[Any, str | None, str | None]:
    """Return (cleaned_value, error_code, message) for a single field."""
    value = raw.strip()

    if not value:
        if spec.required:
            return None, "required_missing", f"'{spec.name}' is required"
        return None, None, None

    if spec.kind == "email":
        normalized = value.lower()
        if not _is_valid_email(normalized):
            return None, "invalid_email", f"'{spec.name}' is not a valid email address"
        return normalized, None, None

    if spec.kind == "number":
        try:
            number = float(value)
        except ValueError:
            return None, "invalid_number", f"'{spec.name}' is not a valid number"
        if spec.min_value is not None and number < spec.min_value:
            return None, "below_minimum", f"'{spec.name}' must be >= {spec.min_value}"
        return number, None, None

    if spec.kind == "date":
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None, "invalid_date", f"'{spec.name}' must use the YYYY-MM-DD format"
        return parsed.isoformat(), None, None

    if spec.kind == "enum":
        if value not in spec.choices:
            return (
                None,
                "invalid_choice",
                f"'{spec.name}' must be one of: {', '.join(spec.choices)}",
            )
        return value, None, None

    # Default: plain string
    if spec.max_length is not None and len(value) > spec.max_length:
        return None, "too_long", f"'{spec.name}' exceeds {spec.max_length} characters"
    return value, None, None


def validate_row(
    row: dict[str, str],
    row_number: int,
    schema: tuple[FieldSpec, ...] = RECORD_SCHEMA,
) -> RowResult:
    """Validate and normalize a single row against the schema."""
    result = RowResult(cleaned={})
    for spec in schema:
        raw = row.get(spec.name, "")
        cleaned_value, error_code, message = _validate_field(spec, raw)
        if error_code is not None:
            result.errors.append(
                {
                    "row_number": row_number,
                    "column_name": spec.name,
                    "error_code": error_code,
                    "message": message,
                }
            )
        elif cleaned_value is not None:
            result.cleaned[spec.name] = cleaned_value
    return result
