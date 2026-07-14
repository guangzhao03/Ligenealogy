"""add person address longitude and latitude

Revision ID: 010_person_address_geo
Revises: 009_geo_places
Create Date: 2026-07-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_person_address_geo"
down_revision: Union[str, Sequence[str], None] = "009_geo_places"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("address_lng", sa.Numeric(10, 6), nullable=True),
    )
    op.add_column(
        "persons",
        sa.Column("address_lat", sa.Numeric(10, 6), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persons", "address_lat")
    op.drop_column("persons", "address_lng")
