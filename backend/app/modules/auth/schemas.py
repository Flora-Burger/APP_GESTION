"""Schemas Pydantic pour l'authentification."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.modules.auth.identifiant import normaliser_identifiant


class RoleUtilisateur(str, Enum):
    """Roles disponibles."""

    ADMIN = "admin"
    USER = "user"


class UtilisateurCreate(BaseModel):
    """Creation d'un compte."""

    email: str = Field(min_length=3, max_length=3)
    mot_de_passe: str = Field(min_length=3, max_length=128)
    nom: str = Field(min_length=1, max_length=200)
    role: RoleUtilisateur = RoleUtilisateur.USER

    @field_validator("email", mode="before")
    @classmethod
    def valider_identifiant(cls, valeur: str) -> str:
        """Identifiant numerique sur 3 chiffres."""
        if not isinstance(valeur, str):
            raise ValueError("identifiant_invalide")
        return normaliser_identifiant(valeur)

    @field_validator("nom")
    @classmethod
    def valider_nom(cls, valeur: str) -> str:
        """Normalise le nom affiche."""
        nom = valeur.strip()
        if not nom:
            raise ValueError("nom_obligatoire")
        return nom


class UtilisateurUpdate(BaseModel):
    """Modification d'un compte par un administrateur."""

    email: str = Field(min_length=3, max_length=3)
    nom: str = Field(min_length=1, max_length=200)
    mot_de_passe: str | None = Field(default=None, min_length=3, max_length=128)
    role: RoleUtilisateur

    @field_validator("email", mode="before")
    @classmethod
    def valider_identifiant(cls, valeur: str) -> str:
        """Identifiant numerique sur 3 chiffres."""
        if not isinstance(valeur, str):
            raise ValueError("identifiant_invalide")
        return normaliser_identifiant(valeur)

    @field_validator("mot_de_passe", mode="before")
    @classmethod
    def valider_mot_de_passe_optionnel(cls, valeur: str | None) -> str | None:
        """Conserve None si le mot de passe n'est pas modifie."""
        if valeur is None:
            return None
        if isinstance(valeur, str) and not valeur.strip():
            return None
        return valeur

    @field_validator("nom")
    @classmethod
    def valider_nom(cls, valeur: str) -> str:
        """Le nom affiche est obligatoire."""
        nom = valeur.strip()
        if not nom:
            raise ValueError("nom_obligatoire")
        return nom


class UtilisateurResponse(BaseModel):
    """Reponse publique d'un utilisateur (sans mot de passe)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom: str | None
    role: RoleUtilisateur
    est_actif: bool
    cree_le: datetime


class TokenPayload(BaseModel):
    """Contenu du token JWT."""

    sub: str
    role: str
    uid: int
