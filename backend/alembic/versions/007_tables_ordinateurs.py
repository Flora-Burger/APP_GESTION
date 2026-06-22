"""Migration : tables ordinateurs et evenements.

Revision ID: 007
Revises: 006
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ordinateurs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("marque", sa.String(length=100), nullable=False),
        sa.Column("modele", sa.String(length=150), nullable=False),
        sa.Column("utilisateur_assigne", sa.String(length=150), nullable=True),
        sa.Column("localisation", sa.String(length=200), nullable=False),
        sa.Column("photo_url", sa.String(length=500), nullable=False),
        sa.Column("statut", sa.String(length=30), nullable=False),
        sa.Column("systeme_exploitation", sa.String(length=100), nullable=True),
        sa.Column("processeur", sa.String(length=150), nullable=True),
        sa.Column("memoire_ram", sa.String(length=50), nullable=True),
        sa.Column("capacite_stockage", sa.String(length=100), nullable=True),
        sa.Column("date_acquisition", sa.Date(), nullable=True),
        sa.Column("garantie", sa.String(length=200), nullable=True),
        sa.Column("cree_le", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nom"),
        sa.UniqueConstraint("numero_serie"),
    )

    op.create_table(
        "ordinateur_evenements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ordinateur_id", sa.Integer(), nullable=False),
        sa.Column("date_evenement", sa.Date(), nullable=False),
        sa.Column("type_evenement", sa.String(length=40), nullable=False),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("utilisateur_responsable", sa.String(length=150), nullable=True),
        sa.ForeignKeyConstraint(
            ["ordinateur_id"], ["ordinateurs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ordinateur_evenements")
    op.drop_table("ordinateurs")
