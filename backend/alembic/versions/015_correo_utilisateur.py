"""Ajoute le correo electronique aux utilisateurs.

Revision ID: 015
Revises: 014
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.add_column(sa.Column("correo", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.drop_column("correo")
