"""Couche d'acces aux donnees pour le module imprimantes."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.modules.imprimantes.modeles import Imprimante, ImprimanteEvenement


class ImprimanteRepository:
    """Repository pour les operations CRUD sur les imprimantes."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir_tous(self) -> list[Imprimante]:
        """Retourne toutes les imprimantes avec leurs evenements."""
        stmt = (
            select(Imprimante)
            .options(joinedload(Imprimante.evenements))
            .order_by(Imprimante.nom)
        )
        return list(self.session.scalars(stmt).unique().all())

    def obtenir_par_id(self, imprimante_id: int) -> Imprimante | None:
        """Retourne une imprimante par son identifiant."""
        stmt = (
            select(Imprimante)
            .options(joinedload(Imprimante.evenements))
            .where(Imprimante.id == imprimante_id)
        )
        return self.session.scalars(stmt).unique().first()

    def obtenir_par_nom(self, nom: str) -> Imprimante | None:
        """Retourne une imprimante par son nom."""
        stmt = select(Imprimante).where(Imprimante.nom == nom.strip())
        return self.session.scalars(stmt).first()

    def creer(self, imprimante: Imprimante) -> Imprimante:
        """Persiste une nouvelle imprimante."""
        self.session.add(imprimante)
        self.session.commit()
        self.session.refresh(imprimante)
        return imprimante

    def sauvegarder(self, imprimante: Imprimante) -> Imprimante:
        """Persiste les modifications."""
        self.session.commit()
        self.session.refresh(imprimante)
        return imprimante

    def supprimer(self, imprimante: Imprimante) -> None:
        """Supprime une imprimante et son historique."""
        self.session.delete(imprimante)
        self.session.commit()

    def ajouter_evenement(self, evenement: ImprimanteEvenement) -> ImprimanteEvenement:
        """Ajoute un evenement a l'historique."""
        self.session.add(evenement)
        self.session.flush()
        return evenement

    def rechercher(self, terme: str) -> list[Imprimante]:
        """Recherche textuelle sur les imprimantes."""
        if not terme.strip():
            return self.obtenir_tous()

        pattern = f"%{terme.strip()}%"
        stmt = (
            select(Imprimante)
            .options(joinedload(Imprimante.evenements))
            .where(
                or_(
                    Imprimante.nom.ilike(pattern),
                    Imprimante.modele.ilike(pattern),
                    Imprimante.localisation.ilike(pattern),
                )
            )
            .order_by(Imprimante.nom)
        )
        return list(self.session.scalars(stmt).unique().all())
