"""Schemas Pydantic pour le module imprimantes."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StatutImprimante(str, Enum):
    """Statut operationnel d'une imprimante."""

    OK = "ok"
    PANNE = "panne"
    MAINTENANCE = "maintenance"


class TypeEvenement(str, Enum):
    """Types d'evenements historiques."""

    COMPTEUR = "compteur"
    TONER = "toner"
    MAINTENANCE = "maintenance"
    MAINTENANCE_TERMINEE = "maintenance_terminee"
    PANNE = "panne"
    REPARATION = "reparation"


class FiltreStatutImprimante(str, Enum):
    """Filtre par statut pour la liste."""

    OK = "ok"
    PANNE = "panne"
    MAINTENANCE = "maintenance"


class ImprimanteCreate(BaseModel):
    """Creation d'une imprimante."""

    nom: str = Field(..., max_length=100)
    modele: str = Field(..., max_length=150)
    localisation: str = Field(..., max_length=200)
    compteur_initial: int = Field(default=0, ge=0)


class ImprimanteUpdate(BaseModel):
    """Modification des donnees maitres (statut deduit des evenements)."""

    nom: str = Field(..., max_length=100)
    modele: str = Field(..., max_length=150)
    localisation: str = Field(..., max_length=200)


class EvenementCreate(BaseModel):
    """Enregistrement d'un evenement ponctuel."""

    date_evenement: date
    type_evenement: TypeEvenement
    compteur_pages: int | None = Field(default=None, ge=0)
    commentaire: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valider_compteur_obligatoire(self) -> "EvenementCreate":
        """Le compteur est obligatoire pour une mise a jour compteur."""
        if self.type_evenement == TypeEvenement.COMPTEUR and self.compteur_pages is None:
            raise ValueError("compteur_obligatoire")
        return self


class EvenementResponse(BaseModel):
    """Reponse pour un evenement historique."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    imprimante_id: int
    date_evenement: date
    type_evenement: TypeEvenement
    compteur_pages: int | None
    commentaire: str | None


class ImprimanteResponse(BaseModel):
    """Reponse API pour une imprimante."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    modele: str
    localisation: str
    statut: StatutImprimante
    compteur_pages: int
    date_dernier_toner: date | None
    date_derniere_maintenance: date | None
    cree_le: datetime


class ImprimanteDetailResponse(ImprimanteResponse):
    """Detail avec historique des evenements."""

    evenements: list[EvenementResponse] = []


class ResultatRecherche(BaseModel):
    """Resultat de recherche globale."""

    module_id: str
    module_libelle: str
    titre: str
    sous_titre: str
    route_web: str
