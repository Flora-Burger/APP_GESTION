"""Reinitialise les donnees vehicules du jour (journaux + immobilisations du jour)."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from backend.app.core.database import SessionLocal
from backend.app.modules.vehicules.modeles import VehiculeImmobilisation, VehiculeJournal


def reinitialiser_journee(jour: date) -> None:
    """Supprime les entrees du jour (journaux et immobilisations demarrees ce jour)."""
    session = SessionLocal()
    try:
        journaux = list(
            session.scalars(
                select(VehiculeJournal).where(VehiculeJournal.date_jour == jour)
            ).all()
        )
        immobilisations = list(
            session.scalars(
                select(VehiculeImmobilisation).where(
                    VehiculeImmobilisation.date_debut == jour
                )
            ).all()
        )

        for journal in journaux:
            session.delete(journal)
        for immobilisation in immobilisations:
            session.delete(immobilisation)

        session.flush()

        session.commit()

        print(f"Date: {jour.isoformat()}")
        print(f"Journaux supprimes: {len(journaux)}")
        print(f"Immobilisations supprimees: {len(immobilisations)}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reinitialise les donnees vehicules d'une journee."
    )
    parser.add_argument(
        "--date",
        dest="date_jour",
        default=date.today().isoformat(),
        help="Date au format AAAA-MM-JJ (defaut: aujourd'hui)",
    )
    args = parser.parse_args()
    jour = date.fromisoformat(args.date_jour)
    reinitialiser_journee(jour)


if __name__ == "__main__":
    main()
