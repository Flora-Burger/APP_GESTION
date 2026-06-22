"""Migration : suppression des colonnes kilometrage vehicules.

Revision ID: 010
Revises: 009
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.drop_column("kilometrage_actuel")
        batch_op.drop_column("kilometrage_jour")

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("kilometrage_de_base")
        batch_op.drop_column("kilometrage")

    with op.batch_alter_table("vehicule_immobilisations") as batch_op:
        batch_op.drop_column("kilometrage_retour")


def downgrade() -> None:
    with op.batch_alter_table("vehicule_immobilisations") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage_retour", sa.Integer(), nullable=True)
        )

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "kilometrage_de_base",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )

    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage_jour", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "kilometrage_actuel",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
