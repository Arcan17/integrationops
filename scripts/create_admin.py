"""Create an initial user (default role: admin).

Usage:
    python scripts/create_admin.py --email admin@example.com --password secret123
    python scripts/create_admin.py --email op@example.com --password secret123 --role operator
"""

import argparse

from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.schemas.user import UserCreate
from app.services.user import create_user, get_user_by_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an IntegrationOps user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--role",
        default=UserRole.admin.value,
        choices=[r.value for r in UserRole],
    )
    parser.add_argument("--full-name", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if get_user_by_email(db, args.email) is not None:
            print(f"User '{args.email}' already exists; nothing to do.")
            return
        user = create_user(
            db,
            UserCreate(email=args.email, password=args.password, full_name=args.full_name),
            role=UserRole(args.role),
        )
        print(f"Created user id={user.id} email={user.email} role={user.role.value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
