"""Couche d'acces aux donnees pour les utilisateurs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.modules.auth.modeles import Utilisateur


class UtilisateurRepository:
    """Repository CRUD pour les comptes utilisateurs."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir_par_email(self, email: str) -> Utilisateur | None:
        """Retourne un utilisateur par email."""
        stmt = select(Utilisateur).where(Utilisateur.email == email.strip())
        return self.session.scalars(stmt).first()

    def obtenir_par_id(self, utilisateur_id: int) -> Utilisateur | None:
        """Retourne un utilisateur par identifiant."""
        stmt = select(Utilisateur).where(Utilisateur.id == utilisateur_id)
        return self.session.scalars(stmt).first()

    def obtenir_tous(self) -> list[Utilisateur]:
        """Liste tous les utilisateurs."""
        stmt = select(Utilisateur).order_by(Utilisateur.email)
        return list(self.session.scalars(stmt).all())

    def compter_admins_actifs(self) -> int:
        """Compte les administrateurs actifs."""
        stmt = select(Utilisateur).where(
            Utilisateur.role == "admin",
            Utilisateur.est_actif.is_(True),
        )
        return len(list(self.session.scalars(stmt).all()))

    def creer(self, utilisateur: Utilisateur) -> Utilisateur:
        """Persiste un nouvel utilisateur."""
        self.session.add(utilisateur)
        self.session.commit()
        self.session.refresh(utilisateur)
        return utilisateur

    def sauvegarder(self, utilisateur: Utilisateur) -> Utilisateur:
        """Persiste les modifications."""
        self.session.commit()
        self.session.refresh(utilisateur)
        return utilisateur

    def supprimer(self, utilisateur: Utilisateur) -> None:
        """Supprime un utilisateur."""
        self.session.delete(utilisateur)
        self.session.commit()
