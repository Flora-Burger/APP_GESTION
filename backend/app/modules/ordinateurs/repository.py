"""Couche d'acces aux donnees pour le module ordinateurs."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.modules.ordinateurs.modeles import Ordinateur, OrdinateurEvenement


class OrdinateurRepository:
    """Repository pour les operations CRUD sur les ordinateurs."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir_tous(self) -> list[Ordinateur]:
        """Retourne tous les ordinateurs avec leurs evenements."""
        stmt = (
            select(Ordinateur)
            .options(joinedload(Ordinateur.evenements))
            .order_by(Ordinateur.nom)
        )
        return list(self.session.scalars(stmt).unique().all())

    def obtenir_par_id(self, ordinateur_id: int) -> Ordinateur | None:
        """Retourne un ordinateur par son identifiant."""
        stmt = (
            select(Ordinateur)
            .options(joinedload(Ordinateur.evenements))
            .where(Ordinateur.id == ordinateur_id)
        )
        return self.session.scalars(stmt).unique().first()

    def obtenir_par_nom(self, nom: str) -> Ordinateur | None:
        """Retourne un ordinateur par son nom."""
        stmt = select(Ordinateur).where(Ordinateur.nom == nom.strip())
        return self.session.scalars(stmt).first()

    def obtenir_par_numero_serie(self, numero_serie: str) -> Ordinateur | None:
        """Retourne un ordinateur par son numero de serie."""
        serie = numero_serie.strip()
        if not serie:
            return None
        stmt = select(Ordinateur).where(Ordinateur.numero_serie == serie)
        return self.session.scalars(stmt).first()

    def creer(self, ordinateur: Ordinateur) -> Ordinateur:
        """Persiste un nouvel ordinateur."""
        self.session.add(ordinateur)
        self.session.commit()
        self.session.refresh(ordinateur)
        return ordinateur

    def sauvegarder(self, ordinateur: Ordinateur) -> Ordinateur:
        """Persiste les modifications."""
        self.session.commit()
        self.session.refresh(ordinateur)
        return ordinateur

    def supprimer(self, ordinateur: Ordinateur) -> None:
        """Supprime un ordinateur et son historique."""
        self.session.delete(ordinateur)
        self.session.commit()

    def ajouter_evenement(self, evenement: OrdinateurEvenement) -> OrdinateurEvenement:
        """Ajoute un evenement a l'historique."""
        self.session.add(evenement)
        self.session.flush()
        return evenement

    def rechercher(self, terme: str) -> list[Ordinateur]:
        """Recherche textuelle sur les ordinateurs."""
        if not terme.strip():
            return self.obtenir_tous()

        pattern = f"%{terme.strip()}%"
        stmt = (
            select(Ordinateur)
            .options(joinedload(Ordinateur.evenements))
            .where(
                or_(
                    Ordinateur.nom.ilike(pattern),
                    Ordinateur.numero_serie.ilike(pattern),
                    Ordinateur.marque.ilike(pattern),
                    Ordinateur.modele.ilike(pattern),
                    Ordinateur.utilisateur_assigne.ilike(pattern),
                    Ordinateur.localisation.ilike(pattern),
                    Ordinateur.systeme_exploitation.ilike(pattern),
                )
            )
            .order_by(Ordinateur.nom)
        )
        return list(self.session.scalars(stmt).unique().all())
