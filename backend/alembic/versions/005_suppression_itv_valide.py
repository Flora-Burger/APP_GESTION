"""Migration : suppression colonne legacy itv_valide.

Revision ID: 005
Revises: 004
Create Date: 2026-06-15

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("itv_valide")


def downgrade() -> None:
    import sqlalchemy as sa

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(sa.Column("itv_valide", sa.Boolean(), nullable=False, server_default="1"))
