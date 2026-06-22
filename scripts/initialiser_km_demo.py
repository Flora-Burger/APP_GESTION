"""Initialise le kilometrage des vehicules fictifs de demonstration."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from backend.app.core.database import SessionLocal
from backend.app.modules.vehicules.modeles import Vehicule, VehiculeJournal

KM_PAR_MATRICULE = {
    "1234-ABC": 45185,
    "5678-DEF": 78045,
    "9012-GHI": 120430,
    "3456-JKL": 32000,
    "7890-MNO": 55142,
}

JOURNAUX_KM = {
    "1234-ABC": [
        {"offset": 1, "km_jour": 120},
        {"offset": 0, "km_jour": 85},
    ],
    "5678-DEF": [
        {"offset": 1, "km_jour": 0},
        {"offset": 0, "km_jour": 45},
    ],
    "9012-GHI": [
        {"offset": 1, "km_jour": 180},
        {"offset": 0, "km_jour": 250},
    ],
    "3456-JKL": [
        {"offset": 0, "km_jour": 0},
    ],
    "7890-MNO": [
        {"offset": 1, "km_jour": 42},
        {"offset": 0, "km_jour": 35},
    ],
}


def initialiser_km_demo() -> None:
    """Met a jour le kilometrage actuel et l'historique journalier de demo."""
    session = SessionLocal()
    aujourdhui = date.today()
    try:
        for matricule, km_actuel in KM_PAR_MATRICULE.items():
            vehicule = session.scalars(
                select(Vehicule).where(Vehicule.matricule == matricule)
            ).first()
            if vehicule is None:
                print(f"Ignorer {matricule} : vehicule introuvable")
                continue

            vehicule.kilometrage_actuel = km_actuel

            entrees = JOURNAUX_KM.get(matricule, [])
            total_km_jour = sum(e["km_jour"] for e in entrees)
            km_cumul = km_actuel - total_km_jour

            for entree in sorted(entrees, key=lambda e: e["offset"], reverse=True):
                jour = aujourdhui - timedelta(days=entree["offset"])
                journal = session.scalars(
                    select(VehiculeJournal).where(
                        VehiculeJournal.vehicule_id == vehicule.id,
                        VehiculeJournal.date_jour == jour,
                    )
                ).first()
                if journal is None:
                    continue
                km_cumul += entree["km_jour"]
                journal.kilometrage_jour = entree["km_jour"]
                journal.kilometrage_actuel = km_cumul

            print(f"{matricule} : km actuel = {km_actuel}")

        session.commit()
        print("Kilometrage de demonstration initialise.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    initialiser_km_demo()
