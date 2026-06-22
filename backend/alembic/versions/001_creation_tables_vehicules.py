"""Creation des tables vehicules et vehicule_journaux

Revision ID: 001
Revises:
Create Date: 2026-06-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("matricule", sa.String(length=20), nullable=False),
        sa.Column("marque", sa.String(length=100), nullable=False),
        sa.Column("modele", sa.String(length=100), nullable=False),
        sa.Column("photo_url", sa.String(length=500), nullable=False),
        sa.Column("itv_valide", sa.Boolean(), nullable=False),
        sa.Column("kilometrage", sa.Integer(), nullable=False),
        sa.Column("consommation_moyenne", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matricule"),
    )
    op.create_table(
        "vehicule_journaux",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicule_id", sa.Integer(), nullable=False),
        sa.Column("date_jour", sa.Date(), nullable=False),
        sa.Column("utilisateur", sa.String(length=200), nullable=True),
        sa.Column("kilometrage_jour", sa.Integer(), nullable=False),
        sa.Column("consommation_jour", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["vehicule_id"], ["vehicules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicule_id", "date_jour", name="uq_vehicule_date"),
    )


def downgrade() -> None:
    op.drop_table("vehicule_journaux")
    op.drop_table("vehicules")
