"""Couche d'acces aux donnees pour le module vehicules."""

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.modules.vehicules.modeles import Vehicule, VehiculeImmobilisation, VehiculeJournal


class VehiculeRepository:
    """Repository pour les operations CRUD sur les vehicules."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir_tous(self) -> list[Vehicule]:
        """Retourne tous les vehicules avec leurs journaux."""
        stmt = (
            select(Vehicule)
            .options(
                joinedload(Vehicule.journaux),
                joinedload(Vehicule.immobilisations),
            )
            .order_by(Vehicule.matricule)
        )
        return list(self.session.scalars(stmt).unique().all())

    def obtenir_par_id(self, vehicule_id: int) -> Vehicule | None:
        """Retourne un vehicule par son identifiant."""
        stmt = (
            select(Vehicule)
            .options(
                joinedload(Vehicule.journaux),
                joinedload(Vehicule.immobilisations),
            )
            .where(Vehicule.id == vehicule_id)
        )
        return self.session.scalars(stmt).unique().first()

    def obtenir_par_matricule(self, matricule: str) -> Vehicule | None:
        """Retourne un vehicule par sa matricule."""
        stmt = select(Vehicule).where(Vehicule.matricule == matricule)
        return self.session.scalars(stmt).first()

    def creer(self, vehicule: Vehicule) -> Vehicule:
        """Persiste un nouveau vehicule."""
        self.session.add(vehicule)
        self.session.commit()
        self.session.refresh(vehicule)
        return vehicule

    def sauvegarder(self, vehicule: Vehicule) -> Vehicule:
        """Persiste les modifications d'un vehicule."""
        self.session.commit()
        self.session.refresh(vehicule)
        return vehicule

    def supprimer(self, vehicule: Vehicule) -> None:
        """Supprime un vehicule et ses journaux (cascade)."""
        self.session.delete(vehicule)
        self.session.commit()

    def obtenir_journal_par_date(
        self, vehicule_id: int, date_jour: date
    ) -> VehiculeJournal | None:
        """Retourne l'entree journaliere active pour une date donnee."""
        return self.obtenir_journal_actif(vehicule_id, date_jour)

    def obtenir_journal_actif(
        self, vehicule_id: int, date_jour: date
    ) -> VehiculeJournal | None:
        """Retourne l'utilisation active pour une date (utilisateur renseigne)."""
        stmt = (
            select(VehiculeJournal)
            .where(
                VehiculeJournal.vehicule_id == vehicule_id,
                VehiculeJournal.date_jour == date_jour,
                VehiculeJournal.actif.is_(True),
                VehiculeJournal.utilisateur.isnot(None),
                func.trim(VehiculeJournal.utilisateur) != "",
            )
            .order_by(VehiculeJournal.id.desc())
        )
        return self.session.scalars(stmt).first()

    def obtenir_journal_par_utilisateur(
        self, vehicule_id: int, date_jour: date, utilisateur: str
    ) -> VehiculeJournal | None:
        """Retourne l'entree d'un utilisateur pour une date."""
        stmt = (
            select(VehiculeJournal)
            .where(
                VehiculeJournal.vehicule_id == vehicule_id,
                VehiculeJournal.date_jour == date_jour,
                VehiculeJournal.utilisateur == utilisateur,
            )
            .order_by(VehiculeJournal.id.desc())
        )
        return self.session.scalars(stmt).first()

    def ajouter_journal(self, journal: VehiculeJournal) -> VehiculeJournal:
        """Ajoute une entree journaliere."""
        self.session.add(journal)
        self.session.commit()
        self.session.refresh(journal)
        return journal

    def sauvegarder_journal(self, journal: VehiculeJournal) -> VehiculeJournal:
        """Persiste les modifications d'une entree journaliere."""
        self.session.commit()
        self.session.refresh(journal)
        return journal

    def rechercher(self, terme: str) -> list[Vehicule]:
        """Recherche textuelle sur les donnees maitres et l'utilisateur du jour."""
        if not terme.strip():
            return self.obtenir_tous()

        pattern = f"%{terme.strip()}%"
        jour = date.today()
        sous_requete_utilisateur = (
            select(VehiculeJournal.vehicule_id)
            .where(
                VehiculeJournal.utilisateur.ilike(pattern),
                VehiculeJournal.date_jour == jour,
            )
            .distinct()
        )
        stmt = (
            select(Vehicule)
            .options(
                joinedload(Vehicule.journaux),
                joinedload(Vehicule.immobilisations),
            )
            .where(
                or_(
                    Vehicule.matricule.ilike(pattern),
                    Vehicule.marque.ilike(pattern),
                    Vehicule.modele.ilike(pattern),
                    Vehicule.id.in_(sous_requete_utilisateur),
                )
            )
            .order_by(Vehicule.matricule)
        )
        return list(self.session.scalars(stmt).unique().all())

    def obtenir_garages_connus(self) -> list[str]:
        """Liste les noms de garage deja utilises."""
        stmt = (
            select(VehiculeImmobilisation.garage)
            .distinct()
            .order_by(VehiculeImmobilisation.garage)
        )
        return [valeur for valeur in self.session.scalars(stmt).all() if valeur]

    def ajouter_immobilisation(
        self, immobilisation: VehiculeImmobilisation
    ) -> VehiculeImmobilisation:
        """Enregistre une immobilisation."""
        self.session.add(immobilisation)
        self.session.commit()
        self.session.refresh(immobilisation)
        return immobilisation

    def sauvegarder_immobilisation(
        self, immobilisation: VehiculeImmobilisation
    ) -> VehiculeImmobilisation:
        """Persiste une immobilisation."""
        self.session.commit()
        self.session.refresh(immobilisation)
        return immobilisation
