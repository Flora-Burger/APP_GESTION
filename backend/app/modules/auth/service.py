"""Logique metier d'authentification et gestion des comptes."""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.securite import (
    creer_token_acces,
    hasher_mot_de_passe,
    verifier_mot_de_passe,
)
from backend.app.modules.auth.identifiant import normaliser_identifiant
from backend.app.modules.auth.modeles import Utilisateur
from backend.app.modules.auth.repository import UtilisateurRepository
from backend.app.modules.auth.schemas import RoleUtilisateur, UtilisateurCreate, UtilisateurResponse, UtilisateurUpdate

logger = logging.getLogger(__name__)

ADMIN_DEFAUT_IDENTIFIANT = "001"
ADMIN_DEFAUT_MOT_DE_PASSE = "admin123"


class AuthService:
    """Service d'authentification et administration des comptes."""

    def __init__(self, session: Session):
        self.repo = UtilisateurRepository(session)

    def initialiser_admin_par_defaut(self) -> None:
        """Cree l'administrateur par defaut si aucun compte n'existe."""
        if self.repo.obtenir_par_email(ADMIN_DEFAUT_IDENTIFIANT):
            return

        admin = Utilisateur(
            email=ADMIN_DEFAUT_IDENTIFIANT,
            mot_de_passe_hash=hasher_mot_de_passe(ADMIN_DEFAUT_MOT_DE_PASSE),
            nom="Administrateur",
            role=RoleUtilisateur.ADMIN.value,
            est_actif=True,
        )
        self.repo.creer(admin)
        logger.info("Compte administrateur par defaut cree (%s)", ADMIN_DEFAUT_IDENTIFIANT)

    def authentifier(self, email: str, mot_de_passe: str) -> tuple[Utilisateur, str]:
        """Authentifie un utilisateur et retourne le token JWT."""
        try:
            identifiant = normaliser_identifiant(email)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        utilisateur = self.repo.obtenir_par_email(identifiant)
        if utilisateur is None or not verifier_mot_de_passe(
            mot_de_passe, utilisateur.mot_de_passe_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="identifiants_invalides",
            )

        if not utilisateur.est_actif:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="compte_desactive",
            )

        token = creer_token_acces(utilisateur.email, utilisateur.role, utilisateur.id)
        return utilisateur, token

    def obtenir_utilisateur_actif(self, utilisateur_id: int) -> Utilisateur:
        """Retourne un utilisateur actif ou leve une erreur."""
        utilisateur = self.repo.obtenir_par_id(utilisateur_id)
        if utilisateur is None or not utilisateur.est_actif:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="utilisateur_invalide",
            )
        return utilisateur

    def lister_utilisateurs(self) -> list[UtilisateurResponse]:
        """Liste tous les comptes."""
        return [
            UtilisateurResponse.model_validate(u) for u in self.repo.obtenir_tous()
        ]

    def lister_contacts_entreprise(self) -> dict[str, list[dict]]:
        """Liste les contacts actifs separes par role."""
        contacts = [
            {
                "id": u.id,
                "email": u.email,
                "nom": (u.nom or u.email).strip(),
                "telefono": (u.telefono or "").strip(),
                "correo": (u.correo or "").strip(),
                "est_admin": u.role == RoleUtilisateur.ADMIN.value,
            }
            for u in self.repo.obtenir_tous()
            if u.est_actif
        ]
        admins = sorted(
            [c for c in contacts if c["est_admin"]],
            key=lambda c: c["nom"].lower(),
        )
        utilisateurs = sorted(
            [c for c in contacts if not c["est_admin"]],
            key=lambda c: c["nom"].lower(),
        )
        return {"admins": admins, "utilisateurs": utilisateurs}

    def creer_utilisateur(self, donnees: UtilisateurCreate) -> UtilisateurResponse:
        """Cree un nouveau compte (admin uniquement)."""
        identifiant = donnees.email
        if self.repo.obtenir_par_email(identifiant):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email_existant",
            )

        utilisateur = Utilisateur(
            email=identifiant,
            mot_de_passe_hash=hasher_mot_de_passe(donnees.mot_de_passe),
            nom=donnees.nom,
            telefono=(donnees.telefono or "").strip() or None,
            correo=(donnees.correo or "").strip() or None,
            role=donnees.role.value,
            est_actif=True,
        )
        utilisateur = self.repo.creer(utilisateur)
        return UtilisateurResponse.model_validate(utilisateur)

    def basculer_actif(
        self, utilisateur_id: int, administrateur_id: int
    ) -> UtilisateurResponse:
        """Active ou desactive un compte."""
        cible = self.repo.obtenir_par_id(utilisateur_id)
        if cible is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="introuvable")

        if cible.id == administrateur_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="auto_desactivation_interdite",
            )

        if cible.role == RoleUtilisateur.ADMIN.value and cible.est_actif:
            if self.repo.compter_admins_actifs() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dernier_admin",
                )

        cible.est_actif = not cible.est_actif
        self.repo.sauvegarder(cible)
        return UtilisateurResponse.model_validate(cible)

    def supprimer_utilisateur(
        self, utilisateur_id: int, administrateur_id: int
    ) -> None:
        """Supprime un compte utilisateur."""
        cible = self.repo.obtenir_par_id(utilisateur_id)
        if cible is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="introuvable")

        if cible.id == administrateur_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="auto_suppression_interdite",
            )

        if cible.role == RoleUtilisateur.ADMIN.value and cible.est_actif:
            if self.repo.compter_admins_actifs() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dernier_admin",
                )

        self.repo.supprimer(cible)

    def modifier_utilisateur(
        self,
        utilisateur_id: int,
        donnees: UtilisateurUpdate,
        administrateur_id: int,
    ) -> UtilisateurResponse:
        """Modifie email, nom, mot de passe et role d'un compte."""
        cible = self.repo.obtenir_par_id(utilisateur_id)
        if cible is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="introuvable")

        identifiant = donnees.email
        autre = self.repo.obtenir_par_email(identifiant)
        if autre is not None and autre.id != utilisateur_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email_existant",
            )

        role_actuel = cible.role
        role_nouveau = donnees.role.value

        if role_actuel == RoleUtilisateur.ADMIN.value and role_nouveau == RoleUtilisateur.USER.value:
            if cible.est_actif and self.repo.compter_admins_actifs() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dernier_admin",
                )

        cible.email = identifiant
        cible.nom = donnees.nom
        cible.telefono = (donnees.telefono or "").strip() or None
        cible.correo = (donnees.correo or "").strip() or None
        cible.role = role_nouveau

        if donnees.mot_de_passe:
            cible.mot_de_passe_hash = hasher_mot_de_passe(donnees.mot_de_passe)

        self.repo.sauvegarder(cible)
        return UtilisateurResponse.model_validate(cible)
