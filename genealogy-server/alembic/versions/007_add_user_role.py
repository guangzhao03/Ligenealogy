"""add user role for RBAC

Revision ID: 007_user_role
Revises: 006_person_nickname
Create Date: 2026-07-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_user_role"
down_revision: Union[str, Sequence[str], None] = "006_person_nickname"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), server_default="member", nullable=False),
    )
    # Family owners become admins so existing accounts keep backend access
    op.execute(
        """
        UPDATE users
        SET role = 'admin'
        WHERE id IN (SELECT DISTINCT owner_id FROM families)
        """
    )
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")
