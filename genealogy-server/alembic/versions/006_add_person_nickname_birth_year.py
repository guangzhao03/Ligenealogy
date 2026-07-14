"""add person nickname birth_year and require generation context

Revision ID: 006_person_nickname
Revises: 005_create_media
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_person_nickname"
down_revision: Union[str, Sequence[str], None] = "005_create_media"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("nickname", sa.String(length=50), server_default="", nullable=False),
    )
    op.add_column("persons", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.alter_column("persons", "nickname", server_default=None)


def downgrade() -> None:
    op.drop_column("persons", "birth_year")
    op.drop_column("persons", "nickname")
