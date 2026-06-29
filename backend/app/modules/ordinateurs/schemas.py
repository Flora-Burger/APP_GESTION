"""Schemas Pydantic pour le module ordinateurs."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.app.modules.ordinateurs.donnees_json import LicenceLogiciel


class StatutOrdinateur(str, Enum):
    """Etat operationnel d'un ordinateur."""

    OK = "ok"
    EN_MAINTENANCE = "en_maintenance"
    EN_PANNE = "en_panne"


class TypeEvenement(str, Enum):
    """Types d'evenements historiques (admin)."""

    ENTRETIEN = "entretien"
    INTERVENTION_TECHNIQUE = "intervention_technique"


class FiltreStatutOrdinateur(str, Enum):
    """Filtre par statut pour la liste."""

    OK = "ok"
    EN_MAINTENANCE = "en_maintenance"
    EN_PANNE = "en_panne"


class OrdinateurCreate(BaseModel):
    """Creation d'un ordinateur (admin)."""

    nom: str = Field(..., max_length=100)
    numero_serie: str | None = Field(default=None, max_length=100)
    marque: str = Field(..., max_length=100)
    modele: str = Field(..., max_length=150)
    utilisateur_assigne: str | None = Field(default=None, max_length=150)
    localisation: str = Field(..., max_length=200)
    systeme_exploitation: str | None = Field(default=None, max_length=100)
    processeur: str | None = Field(default=None, max_length=150)
    memoire_ram: str | None = Field(default=None, max_length=50)
    capacite_stockage: str | None = Field(default=None, max_length=100)
    date_acquisition: date | None = None
    garantie: str | None = Field(default=None, max_length=200)


class OrdinateurUpdate(OrdinateurCreate):
    """Modification des donnees (statut deduit des evenements)."""


class EvenementCreate(BaseModel):
    """Enregistrement d'un evenement ponctuel."""

    date_evenement: date
    type_evenement: TypeEvenement
    commentaire: str | None = Field(default=None, max_length=500)


class EvenementResponse(BaseModel):
    """Reponse pour un evenement historique."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ordinateur_id: int
    date_evenement: date
    type_evenement: str
    commentaire: str | None
    utilisateur_responsable: str | None


class OrdinateurResponse(BaseModel):
    """Reponse API pour un ordinateur."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    numero_serie: str | None
    marque: str
    modele: str
    utilisateur_assigne: str | None
    localisation: str
    statut: StatutOrdinateur
    systeme_exploitation: str | None
    processeur: str | None
    memoire_ram: str | None
    capacite_stockage: str | None
    date_acquisition: date | None
    garantie: str | None
    facture_url: str | None = None
    licences: list[LicenceLogiciel] = []
    cree_le: datetime


class OrdinateurDetailResponse(OrdinateurResponse):
    """Detail avec historique des evenements."""

    evenements: list[EvenementResponse] = []


class ResultatRecherche(BaseModel):
    """Resultat de recherche globale."""

    module_id: str
    module_libelle: str
    titre: str
    sous_titre: str
    route_web: str
