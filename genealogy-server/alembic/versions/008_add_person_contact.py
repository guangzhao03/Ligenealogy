"""add person phone and address

Revision ID: 008_person_contact
Revises: 007_user_role
Create Date: 2026-07-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_person_contact"
down_revision: Union[str, Sequence[str], None] = "007_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("persons", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("persons", sa.Column("address", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("persons", "address")
    op.drop_column("persons", "phone")
