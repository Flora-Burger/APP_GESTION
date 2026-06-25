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
    bind = op.get_bind()
    dialect = bind.dialect.name

    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.add_column(
            sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.drop_constraint("uq_vehicule_date", type_="unique")

    index_kwargs: dict = {
        "unique": True,
    }
    if dialect == "sqlite":
        index_kwargs["sqlite_where"] = sa.text("actif = 1")
    else:
        index_kwargs["postgresql_where"] = sa.text("actif IS TRUE")

    op.create_index(
        "uq_vehicule_date_actif",
        "vehicule_journaux",
        ["vehicule_id", "date_jour"],
        **index_kwargs,
    )


def downgrade() -> None:
    op.drop_index("uq_vehicule_date_actif", table_name="vehicule_journaux")
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.create_unique_constraint("uq_vehicule_date", ["vehicule_id", "date_jour"])
        batch_op.drop_column("actif")
