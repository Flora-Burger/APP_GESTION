"""Migration : kilometrage de base pour coherence historique.

Revision ID: 003
Revises: 002
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.add_column(
            sa.Column("kilometrage_de_base", sa.Integer(), nullable=True)
        )

    op.execute(
        """
        UPDATE vehicules
        SET kilometrage_de_base = kilometrage - COALESCE(
            (SELECT SUM(kilometrage_jour) FROM vehicule_journaux
             WHERE vehicule_journaux.vehicule_id = vehicules.id),
            0
        )
        """
    )
    op.execute(
        """
        UPDATE vehicules
        SET kilometrage_de_base = 0
        WHERE kilometrage_de_base IS NULL OR kilometrage_de_base < 0
        """
    )

    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.alter_column("kilometrage_de_base", nullable=False)

    # Recalculer les snapshots kilometrage_actuel dans l'historique
    conn = op.get_bind()
    vehicules = conn.execute(sa.text("SELECT id, kilometrage_de_base FROM vehicules")).fetchall()
    for vehicule_id, km_base in vehicules:
        journaux = conn.execute(
            sa.text(
                """
                SELECT id, kilometrage_jour FROM vehicule_journaux
                WHERE vehicule_id = :vid ORDER BY date_jour ASC
                """
            ),
            {"vid": vehicule_id},
        ).fetchall()
        cumul = km_base or 0
        for journal_id, km_jour in journaux:
            cumul += km_jour
            conn.execute(
                sa.text(
                    "UPDATE vehicule_journaux SET kilometrage_actuel = :km WHERE id = :jid"
                ),
                {"km": cumul, "jid": journal_id},
            )
        conn.execute(
            sa.text("UPDATE vehicules SET kilometrage = :km WHERE id = :vid"),
            {"km": cumul, "vid": vehicule_id},
        )


def downgrade() -> None:
    with op.batch_alter_table("vehicules") as batch_op:
        batch_op.drop_column("kilometrage_de_base")
