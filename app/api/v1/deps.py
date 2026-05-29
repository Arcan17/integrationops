"""Shared API dependencies: DB session, current user and RBAC guards."""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.user import get_user_by_id

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated, active user from the bearer token."""
    try:
        claims = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise _credentials_exc from exc

    subject = claims.get("sub")
    if subject is None:
        raise _credentials_exc

    user = get_user_by_id(db, int(subject))
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Build a dependency that authorizes only the given roles (admin always allowed)."""

    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is UserRole.admin or current_user.role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this operation",
        )

    return _guard
