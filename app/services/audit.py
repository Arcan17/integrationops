"""Audit logging helper."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_event(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit log entry to the session (caller is responsible for commit)."""
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    return log
