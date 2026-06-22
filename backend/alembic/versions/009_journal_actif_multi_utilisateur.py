"""Migration : journal actif et plusieurs utilisations par jour.

Revision ID: 009
Revises: 008
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.add_column(
            sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.drop_constraint("uq_vehicule_date", type_="unique")

    op.create_index(
        "uq_vehicule_date_actif",
        "vehicule_journaux",
        ["vehicule_id", "date_jour"],
        unique=True,
        sqlite_where=sa.text("actif = 1"),
    )


def downgrade() -> None:
    op.drop_index("uq_vehicule_date_actif", table_name="vehicule_journaux")
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.create_unique_constraint("uq_vehicule_date", ["vehicule_id", "date_jour"])
        batch_op.drop_column("actif")
