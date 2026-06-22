"""Migration : identifiant utilisateur sur 3 chiffres.

Revision ID: 012
Revises: 011
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE utilisateurs SET email = '001' WHERE email = 'admin@admin.com'"
    )

    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            type_=sa.String(length=3),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("utilisateurs") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=3),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    op.execute(
        "UPDATE utilisateurs SET email = 'admin@admin.com' WHERE email = '001'"
    )
