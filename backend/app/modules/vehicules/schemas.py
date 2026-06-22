"""Schemas Pydantic pour le module vehicules."""

from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StatutVehicule(str, Enum):
    """Statut calcule libre/occupe (filtres et compatibilite API)."""

    LIBRE = "libre"
    OCCUPE = "occupe"


class StatutAffichageVehicule(str, Enum):
    """Statut affiche sur la fiche vehicule."""

    DISPONIBLE = "disponible"
    OCCUPE = "occupe"
    NO_DISPONIBLE = "no_disponible"
    AU_GARAGE = "au_garage"


class MotifImmobilisation(str, Enum):
    """Motif d'immobilisation au garage."""

    REVISION = "revision"
    PANNE = "panne"
    ACCIDENT = "accident"
    AUTRE = "autre"


class StatutItv(str, Enum):
    """Statut ITV calcule a partir de la date d'expiration."""

    VALIDE = "valide"
    EXPIRE_BIENTOT = "expire_bientot"
    EXPIREE = "expiree"


class FiltreStatut(str, Enum):
    """Filtre de statut pour la liste."""

    LIBRE = "libre"
    OCCUPE = "occupe"
    AU_GARAGE = "au_garage"


class FiltreItv(str, Enum):
    """Filtre ITV par alerte."""

    VALIDE = "valide"
    EXPIRE_BIENTOT = "expire_bientot"
    EXPIREE = "expiree"


class FiltreKmJour(str, Enum):
    """Filtre par kilometrage du jour."""

    MOINS_30 = "moins_30"
    ENTRE_30_60 = "entre_30_60"
    ENTRE_60_120 = "entre_60_120"
    PLUS_120 = "plus_120"


def kilometrage_jour_correspond_au_filtre(km: int, filtre: FiltreKmJour) -> bool:
    """Verifie si le kilometrage du jour correspond a la tranche demandee."""
    if filtre == FiltreKmJour.MOINS_30:
        return km < 30
    if filtre == FiltreKmJour.ENTRE_30_60:
        return 30 <= km < 60
    if filtre == FiltreKmJour.ENTRE_60_120:
        return 60 <= km <= 120
    if filtre == FiltreKmJour.PLUS_120:
        return km > 120
    return False

class VehiculeBase(BaseModel):
    """Champs communs d'un vehicule."""

    matricule: str = Field(..., max_length=20)
    marque: str = Field(default="", max_length=100)
    modele: str = Field(..., max_length=100)
    photo_url: str = Field(default="", max_length=500)
    date_expiration_itv: date
    consommation_moyenne: Decimal = Field(default=Decimal("0.00"), ge=0)


class VehiculeCreate(VehiculeBase):
    """Schema de creation d'un vehicule."""


class VehiculeCreateAdmin(BaseModel):
    """Creation admin simplifiee (matricule + modele + kilometrage initial)."""

    matricule: str = Field(..., max_length=20)
    modele: str = Field(..., max_length=100)
    kilometrage_actuel: int = Field(..., ge=0)


class VehiculeUpdateAdmin(BaseModel):
    """Modification admin d'un vehicule."""

    matricule: str = Field(..., max_length=20)
    modele: str = Field(..., max_length=100)


class VehiculeJournalBase(BaseModel):
    """Champs communs d'une entree journaliere."""

    date_jour: date
    utilisateur: str | None = Field(default=None, max_length=200)
    kilometrage_actuel: int = Field(default=0, ge=0)
    kilometrage_jour: int = Field(default=0, ge=0)
    consommation_jour: Decimal = Field(default=Decimal("0.00"), ge=0)
    cout_carburant_jour: Decimal = Field(default=Decimal("0.00"), ge=0)


class VehiculeJournalCreate(VehiculeJournalBase):
    """Schema de creation d'une entree journaliere."""


class DonneesJourVehicule(BaseModel):
    """Donnees modifiables pour une journee donnee (sans utilisateur : assignation separee)."""

    date_jour: date
    kilometrage_actuel: int = Field(..., ge=0)
    consommation_jour: Decimal = Field(default=Decimal("0.00"), ge=0)
    cout_carburant_jour: Decimal = Field(default=Decimal("0.00"), ge=0)

    @model_validator(mode="after")
    def valider_carburant_lie(self) -> "DonneesJourVehicule":
        """Litres et cout du plein doivent etre renseignes ensemble."""
        litres = self.consommation_jour
        cout = self.cout_carburant_jour
        if litres > 0 and cout <= 0:
            raise ValueError("carburant_incomplet")
        if cout > 0 and litres <= 0:
            raise ValueError("carburant_incomplet")
        return self


class ItvUpdate(BaseModel):
    """Modification de la date d'expiration ITV."""

    date_expiration_itv: date

    @field_validator("date_expiration_itv")
    @classmethod
    def valider_date_itv(cls, valeur: date) -> date:
        """La date ITV est obligatoire."""
        if valeur is None:
            raise ValueError("La date d'expiration ITV est obligatoire")
        return valeur


class VehiculeJournalResponse(VehiculeJournalBase):
    """Reponse pour une entree journaliere."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicule_id: int


class ImmobilisationCreate(BaseModel):
    """Demande de mise au garage."""

    motif: MotifImmobilisation
    garage: str = Field(..., min_length=1, max_length=200)
    date_debut: date
    date_retour_estimee: date | None = None
    commentaire: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valider_dates(self) -> "ImmobilisationCreate":
        """La date de retour estimee ne peut pas preceder le debut."""
        if (
            self.date_retour_estimee is not None
            and self.date_retour_estimee < self.date_debut
        ):
            raise ValueError("date_retour_invalide")
        return self


class RemiseEnServiceCreate(BaseModel):
    """Cloture d'une immobilisation."""

    date_fin: date | None = None


class ImmobilisationResponse(BaseModel):
    """Immobilisation active ou historique."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicule_id: int
    motif: MotifImmobilisation
    garage: str
    date_debut: date
    date_retour_estimee: date | None = None
    commentaire: str | None = None
    date_fin: date | None = None


class VehiculeResponse(VehiculeBase):
    """Reponse API pour un vehicule avec etat du jour."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    modele_affiche: str
    photo_url_affiche: str
    statut: StatutVehicule
    statut_affichage: StatutAffichageVehicule
    statut_itv: StatutItv
    immobilisation_active: ImmobilisationResponse | None = None
    utilisateur_jour: str | None = None
    kilometrage_actuel: int = 0
    kilometrage_jour_aujourdhui: int = 0
    consommation_jour_aujourdhui: Decimal = Decimal("0.00")
    cout_carburant_jour_aujourdhui: Decimal = Decimal("0.00")
    consommation_session_aujourdhui: Decimal = Decimal("0.00")
    cout_session_aujourdhui: Decimal = Decimal("0.00")


class VehiculeDetailResponse(VehiculeResponse):
    """Reponse detaillee avec historique."""

    journaux: list[VehiculeJournalResponse] = []
    immobilisations: list[ImmobilisationResponse] = []


class ResultatRecherche(BaseModel):
    """Resultat de recherche globale."""

    module_id: str
    module_libelle: str
    titre: str
    sous_titre: str
    route_web: str


def calculer_statut_itv(date_expiration: date, reference: date | None = None) -> StatutItv:
    """Calcule le statut ITV (vert / orange / rouge)."""
    aujourdhui = reference or date.today()
    if date_expiration < aujourdhui:
        return StatutItv.EXPIREE
    if date_expiration <= aujourdhui + timedelta(days=30):
        return StatutItv.EXPIRE_BIENTOT
    return StatutItv.VALIDE
