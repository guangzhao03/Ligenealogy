"""create person_relations table

Revision ID: 004_create_person_relations
Revises: 003_create_persons
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_create_person_relations"
down_revision: Union[str, Sequence[str], None] = "003_create_persons"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "person_relations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.BigInteger(), nullable=False),
        sa.Column("from_person_id", sa.BigInteger(), nullable=False),
        sa.Column("to_person_id", sa.BigInteger(), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(["from_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["to_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "family_id",
            "from_person_id",
            "to_person_id",
            "relation_type",
            name="uk_relation",
        ),
    )
    op.create_index("ix_person_relations_family_id", "person_relations", ["family_id"])
    op.create_index(
        "ix_person_relations_from_person_id", "person_relations", ["from_person_id"]
    )
    op.create_index(
        "ix_person_relations_to_person_id", "person_relations", ["to_person_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_person_relations_to_person_id", table_name="person_relations")
    op.drop_index("ix_person_relations_from_person_id", table_name="person_relations")
    op.drop_index("ix_person_relations_family_id", table_name="person_relations")
    op.drop_table("person_relations")
