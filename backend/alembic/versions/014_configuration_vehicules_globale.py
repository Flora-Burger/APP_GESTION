"""Configuration globale seguro y talleres (todos los vehiculos).

Revision ID: 014
Revises: 013
"""
from typing import Sequence, Union

import json
import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrer_donnees_vehicule_existant(connection) -> None:
    """Copia seguro/talleres du premier vehicule vers la config globale."""
    row = connection.execute(
        sa.text(
            """
            SELECT seguro_compania, seguro_poliza,
                   seguro_tel_asistencia, seguro_tel_grua,
                   seguro_tel_emergencias, seguro_otro_contacto,
                   talleres_referencia
            FROM vehicules
            WHERE seguro_compania IS NOT NULL
               OR seguro_poliza IS NOT NULL
               OR seguro_tel_asistencia IS NOT NULL
               OR talleres_referencia IS NOT NULL
            LIMIT 1
            """
        )
    ).mappings().first()

    if row is None:
        return

    contactos = []
    libelles = [
        ("Asistencia", row.get("seguro_tel_asistencia")),
        ("Grua", row.get("seguro_tel_grua")),
        ("Emergencias", row.get("seguro_tel_emergencias")),
        ("Otro", row.get("seguro_otro_contacto")),
    ]
    for etiqueta, telefono in libelles:
        if telefono and str(telefono).strip():
            contactos.append({"etiqueta": etiqueta, "telefono": str(telefono).strip()})

    connection.execute(
        sa.text(
            """
            UPDATE vehicules_configuration
            SET seguro_compania = :compania,
                seguro_poliza = :poliza,
                seguro_contactos = :contactos,
                talleres_referencia = :talleres
            WHERE id = 1
            """
        ),
        {
            "compania": row.get("seguro_compania"),
            "poliza": row.get("seguro_poliza"),
            "contactos": json.dumps(contactos, ensure_ascii=False) if contactos else None,
            "talleres": row.get("talleres_referencia"),
        },
    )


def upgrade() -> None:
    op.create_table(
        "vehicules_configuration",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seguro_compania", sa.String(length=200), nullable=True),
        sa.Column("seguro_poliza", sa.String(length=100), nullable=True),
        sa.Column("seguro_contactos", sa.Text(), nullable=True),
        sa.Column("talleres_referencia", sa.Text(), nullable=True),
    )
    op.execute("INSERT INTO vehicules_configuration (id) VALUES (1)")

    connection = op.get_bind()
    _migrer_donnees_vehicule_existant(connection)


def downgrade() -> None:
    op.drop_table("vehicules_configuration")
