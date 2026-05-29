"""Add created_by to processing_jobs for ownership.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "processing_jobs",
        sa.Column("created_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_processing_jobs_created_by_users",
        "processing_jobs",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_processing_jobs_created_by", "processing_jobs", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_created_by", table_name="processing_jobs")
    op.drop_constraint(
        "fk_processing_jobs_created_by_users", "processing_jobs", type_="foreignkey"
    )
    op.drop_column("processing_jobs", "created_by")
