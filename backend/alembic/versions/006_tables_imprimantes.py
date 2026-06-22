"""Migration : tables imprimantes et evenements.

Revision ID: 006
Revises: 005
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "imprimantes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("modele", sa.String(length=150), nullable=False),
        sa.Column("localisation", sa.String(length=200), nullable=False),
        sa.Column("statut", sa.String(length=20), nullable=False),
        sa.Column("compteur_pages", sa.Integer(), nullable=False),
        sa.Column("date_dernier_toner", sa.Date(), nullable=True),
        sa.Column("date_derniere_maintenance", sa.Date(), nullable=True),
        sa.Column("cree_le", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nom"),
    )

    op.create_table(
        "imprimante_evenements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("imprimante_id", sa.Integer(), nullable=False),
        sa.Column("date_evenement", sa.Date(), nullable=False),
        sa.Column("type_evenement", sa.String(length=20), nullable=False),
        sa.Column("compteur_pages", sa.Integer(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["imprimante_id"], ["imprimantes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("imprimante_evenements")
    op.drop_table("imprimantes")
