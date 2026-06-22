"""Routes API REST pour le module vehicules."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth_dependances import obtenir_utilisateur_connecte
from backend.app.core.database import obtenir_session
from backend.app.modules.auth.modeles import Utilisateur
from backend.app.modules.vehicules.schemas import (
    DonneesJourVehicule,
    FiltreItv,
    FiltreKmJour,
    FiltreStatut,
    ResultatRecherche,
    VehiculeCreate,
    VehiculeDetailResponse,
    VehiculeJournalResponse,
    VehiculeResponse,
)
from backend.app.modules.vehicules.service import VehiculeService

router = APIRouter(
    tags=["vehicules"],
    dependencies=[Depends(obtenir_utilisateur_connecte)],
)


def _obtenir_service(session: Session = Depends(obtenir_session)) -> VehiculeService:
    return VehiculeService(session)


@router.get("/recherche", response_model=list[ResultatRecherche])
def recherche_globale(
    q: str = Query(default="", min_length=0),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Recherche globale sur tous les modules actifs."""
    return service.rechercher_global(q)


@router.get("/vehicules", response_model=list[VehiculeResponse])
def lister_vehicules(
    recherche: str | None = Query(default=None),
    statut: FiltreStatut | None = Query(default=None),
    itv: FiltreItv | None = Query(default=None),
    km_jour: FiltreKmJour | None = Query(default=None),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Liste les vehicules avec filtres optionnels."""
    return service.lister(recherche, statut, itv, km_jour)


@router.get("/vehicules/{vehicule_id}", response_model=VehiculeDetailResponse)
def obtenir_vehicule(
    vehicule_id: int,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Retourne le detail d'un vehicule avec historique."""
    return service.obtenir_detail(vehicule_id)


@router.post("/vehicules", response_model=VehiculeResponse, status_code=201)
def creer_vehicule(
    donnees: VehiculeCreate,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Cree un nouveau vehicule."""
    return service.creer(donnees)


@router.post(
    "/vehicules/{vehicule_id}/journaux",
    response_model=VehiculeJournalResponse,
    status_code=201,
)
def enregistrer_donnees_jour(
    vehicule_id: int,
    donnees: DonneesJourVehicule,
    utilisateur: Utilisateur = Depends(obtenir_utilisateur_connecte),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Enregistre ou met a jour les donnees journalieres d'un vehicule."""
    return service.enregistrer_donnees_jour(vehicule_id, donnees, utilisateur)
