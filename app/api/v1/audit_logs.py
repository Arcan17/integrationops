"""Audit log query endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get(
    "",
    response_model=list[AuditLogRead],
    summary="List audit logs",
    description="Returns recent operational audit events. Admin only.",
)
def list_audit_logs(
    action: str | None = Query(default=None, description="Filter by exact action name"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> list[AuditLog]:
    """Return audit log entries, most recent first."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    return list(db.scalars(stmt))
