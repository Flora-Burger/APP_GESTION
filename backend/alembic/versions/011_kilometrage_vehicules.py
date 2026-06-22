"""Migration : kilometrage actuel et journalier vehicules.

Revision ID: 011
Revises: 010
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage_actuel", sa.Integer(), nullable=False, server_default="0")
        )

    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage_actuel", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("kilometrage_jour", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.drop_column("kilometrage_jour")
        batch_op.drop_column("kilometrage_actuel")

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("kilometrage_actuel")
