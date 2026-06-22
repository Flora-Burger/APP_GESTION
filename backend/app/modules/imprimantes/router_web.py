"""Routes web (Jinja2 + HTMX) pour le module imprimantes."""

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.imprimantes.schemas import (
    EvenementCreate,
    FiltreStatutImprimante,
    TypeEvenement,
)
from backend.app.modules.imprimantes.service import ImprimanteService

router = APIRouter(tags=["imprimantes-web"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> ImprimanteService:
    return ImprimanteService(session)


def _params_filtres(
    recherche: str | None = None,
    statut: str | None = None,
) -> dict:
    """Convertit les parametres de formulaire en enums."""
    return {
        "recherche": recherche or None,
        "statut": FiltreStatutImprimante(statut) if statut else None,
    }


def _contexte_liste(request: Request, imprimantes, **extra):
    """Contexte commun pour les fragments de liste."""
    return contexte_template(
        request,
        imprimantes=imprimantes,
        date_aujourdhui=date.today().isoformat(),
        types_evenement=TypeEvenement,
        **extra,
    )


@router.get("/imprimantes", response_class=HTMLResponse)
def page_imprimantes(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Page principale de gestion des imprimantes."""
    filtres = _params_filtres(recherche, statut)
    imprimantes = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "imprimantes/liste.html",
        contexte_template(
            request,
            imprimantes=imprimantes,
            filtres_actifs={
                "recherche": recherche or "",
                "statut": statut or "",
            },
            date_aujourdhui=date.today().isoformat(),
            types_evenement=TypeEvenement,
        ),
    )


@router.get("/imprimantes/partials/liste", response_class=HTMLResponse)
def partial_liste_imprimantes(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Fragment HTMX de la liste des imprimantes."""
    filtres = _params_filtres(recherche, statut)
    imprimantes = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "imprimantes/partials/liste_cartes.html",
        _contexte_liste(request, imprimantes),
    )


@router.get("/imprimantes/{imprimante_id}/historique", response_class=HTMLResponse)
def page_historique(
    request: Request,
    imprimante_id: int,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Vue historique des evenements d'une imprimante."""
    detail = service.obtenir_detail(imprimante_id)

    return templates.TemplateResponse(
        request,
        "imprimantes/historique.html",
        contexte_template(request, imprimante=detail),
    )


@router.post("/imprimantes/{imprimante_id}/evenement", response_class=HTMLResponse)
def enregistrer_evenement(
    request: Request,
    imprimante_id: int,
    date_evenement: str = Form(...),
    type_evenement: str = Form(...),
    compteur_pages: str = Form(default=""),
    commentaire: str = Form(default=""),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Enregistre un evenement depuis le formulaire web."""
    message_succes = None
    message_erreur = None

    compteur_val = None
    if compteur_pages.strip():
        try:
            compteur_val = max(0, int(compteur_pages.strip()))
        except ValueError:
            message_erreur = "erreur_evenement"

    if message_erreur is None:
        try:
            donnees = EvenementCreate(
                date_evenement=date.fromisoformat(date_evenement),
                type_evenement=TypeEvenement(type_evenement),
                compteur_pages=compteur_val,
                commentaire=commentaire.strip() or None,
            )
            service.enregistrer_evenement(imprimante_id, donnees)
            message_succes = "evenement_enregistre"
        except ValidationError:
            message_erreur = "compteur_obligatoire"
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "erreur_evenement"
            message_erreur = detail
        except ValueError:
            message_erreur = "erreur_evenement"

    filtres = _params_filtres(recherche or None, statut or None)
    imprimantes = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "imprimantes/partials/liste_cartes.html",
        _contexte_liste(
            request,
            imprimantes,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )
