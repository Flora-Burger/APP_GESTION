"""Migration : table vehicule_immobilisations.

Revision ID: 008
Revises: 007
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicule_immobilisations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicule_id", sa.Integer(), nullable=False),
        sa.Column("motif", sa.String(length=30), nullable=False),
        sa.Column("garage", sa.String(length=200), nullable=False),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_retour_estimee", sa.Date(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("date_fin", sa.Date(), nullable=True),
        sa.Column("kilometrage_retour", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["vehicule_id"], ["vehicules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("vehicule_immobilisations")
