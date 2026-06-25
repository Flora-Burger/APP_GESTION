"""Migration : nouveaux champs vehicules et journaux.

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Date expiration ITV sur vehicules
    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(sa.Column("date_expiration_itv", sa.Date(), nullable=True))

    if dialect == "sqlite":
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = date('now', '+365 days')
            WHERE itv_valide = 1 AND date_expiration_itv IS NULL
            """
        )
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = date('now', '-30 days')
            WHERE itv_valide = 0 AND date_expiration_itv IS NULL
            """
        )
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = date('now', '+365 days')
            WHERE date_expiration_itv IS NULL
            """
        )
    else:
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = CURRENT_DATE + INTERVAL '365 days'
            WHERE itv_valide IS TRUE AND date_expiration_itv IS NULL
            """
        )
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = CURRENT_DATE - INTERVAL '30 days'
            WHERE itv_valide IS FALSE AND date_expiration_itv IS NULL
            """
        )
        op.execute(
            """
            UPDATE vehicules
            SET date_expiration_itv = CURRENT_DATE + INTERVAL '365 days'
            WHERE date_expiration_itv IS NULL
            """
        )

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.alter_column("date_expiration_itv", nullable=False)

    # Nouveaux champs sur journaux
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.add_column(sa.Column("kilometrage_actuel", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("cout_carburant_jour", sa.Numeric(precision=8, scale=2), nullable=True)
        )

    op.execute(
        """
        UPDATE vehicule_journaux
        SET kilometrage_actuel = (
            SELECT kilometrage FROM vehicules WHERE vehicules.id = vehicule_journaux.vehicule_id
        )
        WHERE kilometrage_actuel IS NULL
        """
    )
    op.execute(
        """
        UPDATE vehicule_journaux
        SET cout_carburant_jour = 0
        WHERE cout_carburant_jour IS NULL
        """
    )

    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.alter_column("kilometrage_actuel", nullable=False)
        batch_op.alter_column("cout_carburant_jour", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("vehicule_journaux") as batch_op:
        batch_op.drop_column("cout_carburant_jour")
        batch_op.drop_column("kilometrage_actuel")

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("date_expiration_itv")
