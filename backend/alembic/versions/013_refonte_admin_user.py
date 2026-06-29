"""Migration : refonte admin utilisateur (assignation, seguro, facturas).

Revision ID: 013
Revises: 012
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.add_column(sa.Column("telefono", sa.String(length=30), nullable=True))

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(sa.Column("utilisateur_assigne", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("seguro_compania", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("seguro_poliza", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("seguro_tel_asistencia", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("seguro_tel_grua", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("seguro_tel_emergencias", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("seguro_otro_contacto", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("talleres_referencia", sa.Text(), nullable=True))

    with op.batch_alter_table("imprimantes") as batch_op:
        batch_op.add_column(sa.Column("fecha_compra", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("facture_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("tipo_tinta", sa.String(length=100), nullable=True))

    with op.batch_alter_table("ordinateurs") as batch_op:
        batch_op.add_column(sa.Column("facture_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("licences", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ordinateurs") as batch_op:
        batch_op.drop_column("licences")
        batch_op.drop_column("facture_url")

    with op.batch_alter_table("imprimantes") as batch_op:
        batch_op.drop_column("tipo_tinta")
        batch_op.drop_column("facture_url")
        batch_op.drop_column("fecha_compra")

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("talleres_referencia")
        batch_op.drop_column("seguro_otro_contacto")
        batch_op.drop_column("seguro_tel_emergencias")
        batch_op.drop_column("seguro_tel_grua")
        batch_op.drop_column("seguro_tel_asistencia")
        batch_op.drop_column("seguro_poliza")
        batch_op.drop_column("seguro_compania")
        batch_op.drop_column("utilisateur_assigne")

    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.drop_column("telefono")
