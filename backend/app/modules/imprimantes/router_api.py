"""Routes API REST pour le module imprimantes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth_dependances import obtenir_utilisateur_connecte
from backend.app.core.database import obtenir_session
from backend.app.modules.imprimantes.schemas import (
    EvenementCreate,
    EvenementResponse,
    FiltreStatutImprimante,
    ImprimanteCreate,
    ImprimanteDetailResponse,
    ImprimanteResponse,
    ImprimanteUpdate,
    ResultatRecherche,
)
from backend.app.modules.imprimantes.service import ImprimanteService

router = APIRouter(
    tags=["imprimantes"],
    dependencies=[Depends(obtenir_utilisateur_connecte)],
)


def _obtenir_service(session: Session = Depends(obtenir_session)) -> ImprimanteService:
    return ImprimanteService(session)


@router.get("/imprimantes/recherche", response_model=list[ResultatRecherche])
def recherche_globale(
    q: str = Query(default="", min_length=0),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Recherche globale sur les imprimantes."""
    return service.rechercher_global(q)


@router.get("/imprimantes", response_model=list[ImprimanteResponse])
def lister_imprimantes(
    recherche: str | None = Query(default=None),
    statut: FiltreStatutImprimante | None = Query(default=None),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Liste les imprimantes avec filtres optionnels."""
    return service.lister(recherche, statut)


@router.get("/imprimantes/{imprimante_id}", response_model=ImprimanteDetailResponse)
def obtenir_imprimante(
    imprimante_id: int,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Retourne le detail d'une imprimante avec historique."""
    return service.obtenir_detail(imprimante_id)


@router.post("/imprimantes", response_model=ImprimanteResponse, status_code=201)
def creer_imprimante(
    donnees: ImprimanteCreate,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Cree une nouvelle imprimante."""
    return service.creer(donnees)


@router.put("/imprimantes/{imprimante_id}", response_model=ImprimanteResponse)
def modifier_imprimante(
    imprimante_id: int,
    donnees: ImprimanteUpdate,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Modifie les donnees maitres d'une imprimante."""
    return service.modifier(imprimante_id, donnees)


@router.post(
    "/imprimantes/{imprimante_id}/evenements",
    response_model=EvenementResponse,
    status_code=201,
)
def enregistrer_evenement(
    imprimante_id: int,
    donnees: EvenementCreate,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Enregistre un evenement ponctuel."""
    return service.enregistrer_evenement(imprimante_id, donnees)
