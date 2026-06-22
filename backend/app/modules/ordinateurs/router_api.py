"""Routes API REST pour le module ordinateurs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.auth_dependances import obtenir_utilisateur_connecte
from backend.app.core.database import obtenir_session
from backend.app.modules.ordinateurs.schemas import (
    EvenementCreate,
    EvenementResponse,
    FiltreStatutOrdinateur,
    OrdinateurCreate,
    OrdinateurDetailResponse,
    OrdinateurResponse,
    OrdinateurUpdate,
    ResultatRecherche,
)
from backend.app.modules.ordinateurs.service import OrdinateurService

router = APIRouter(
    tags=["ordinateurs"],
    dependencies=[Depends(obtenir_utilisateur_connecte)],
)


def _obtenir_service(session: Session = Depends(obtenir_session)) -> OrdinateurService:
    return OrdinateurService(session)


@router.get("/ordinateurs/recherche", response_model=list[ResultatRecherche])
def recherche_globale(
    q: str = Query(default="", min_length=0),
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Recherche globale sur les ordinateurs."""
    return service.rechercher_global(q)


@router.get("/ordinateurs", response_model=list[OrdinateurResponse])
def lister_ordinateurs(
    recherche: str | None = Query(default=None),
    statut: FiltreStatutOrdinateur | None = Query(default=None),
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Liste les ordinateurs avec filtres optionnels."""
    return service.lister(recherche, statut)


@router.get("/ordinateurs/{ordinateur_id}", response_model=OrdinateurDetailResponse)
def obtenir_ordinateur(
    ordinateur_id: int,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Retourne le detail d'un ordinateur avec historique."""
    return service.obtenir_detail(ordinateur_id)


@router.post("/ordinateurs", response_model=OrdinateurResponse, status_code=201)
def creer_ordinateur(
    donnees: OrdinateurCreate,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Cree un nouvel ordinateur."""
    return service.creer(donnees)


@router.put("/ordinateurs/{ordinateur_id}", response_model=OrdinateurResponse)
def modifier_ordinateur(
    ordinateur_id: int,
    donnees: OrdinateurUpdate,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Modifie les donnees maitres d'un ordinateur."""
    return service.modifier(ordinateur_id, donnees)


@router.post(
    "/ordinateurs/{ordinateur_id}/evenements",
    response_model=EvenementResponse,
    status_code=201,
)
def enregistrer_evenement(
    ordinateur_id: int,
    donnees: EvenementCreate,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Enregistre un evenement ponctuel."""
    return service.enregistrer_evenement(ordinateur_id, donnees)
