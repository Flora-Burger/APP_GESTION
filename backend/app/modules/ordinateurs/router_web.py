"""Routes web (Jinja2 + HTMX) pour le module ordinateurs."""

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.affichage import peut_enregistrer_evenement
from backend.app.modules.ordinateurs.schemas import (
    EvenementCreate,
    FiltreStatutOrdinateur,
    TypeEvenement,
)
from backend.app.modules.ordinateurs.service import OrdinateurService

router = APIRouter(tags=["ordinateurs-web"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> OrdinateurService:
    return OrdinateurService(session)


def _params_filtres(
    recherche: str | None = None,
    statut: str | None = None,
) -> dict:
    """Convertit les parametres de formulaire en enums."""
    return {
        "recherche": recherche or None,
        "statut": FiltreStatutOrdinateur(statut) if statut else None,
    }


def _contexte_liste(request: Request, ordinateurs, **extra):
    """Contexte commun pour les fragments de liste."""
    return contexte_template(
        request,
        ordinateurs=ordinateurs,
        date_aujourdhui=date.today().isoformat(),
        types_evenement=TypeEvenement,
        **extra,
    )


@router.get("/ordinateurs", response_class=HTMLResponse)
def page_ordinateurs(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    message: str | None = None,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Page principale de gestion des ordinateurs."""
    filtres = _params_filtres(recherche, statut)
    ordinateurs = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "ordinateurs/liste.html",
        contexte_template(
            request,
            ordinateurs=ordinateurs,
            filtres_actifs={
                "recherche": recherche or "",
                "statut": statut or "",
            },
            date_aujourdhui=date.today().isoformat(),
            types_evenement=TypeEvenement,
            message=message,
        ),
    )


@router.get("/ordinateurs/partials/liste", response_class=HTMLResponse)
def partial_liste_ordinateurs(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Fragment HTMX de la liste des ordinateurs."""
    filtres = _params_filtres(recherche, statut)
    ordinateurs = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "ordinateurs/partials/liste_cartes.html",
        _contexte_liste(request, ordinateurs),
    )


@router.get("/ordinateurs/{ordinateur_id}/historique", response_class=HTMLResponse)
def page_historique(
    request: Request,
    ordinateur_id: int,
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Vue historique des evenements d'un ordinateur."""
    detail = service.obtenir_detail(ordinateur_id)

    return templates.TemplateResponse(
        request,
        "ordinateurs/historique.html",
        contexte_template(request, ordinateur=detail),
    )


@router.post("/ordinateurs/{ordinateur_id}/evenement", response_class=HTMLResponse)
def enregistrer_evenement(
    request: Request,
    ordinateur_id: int,
    date_evenement: str = Form(...),
    type_evenement: str = Form(...),
    commentaire: str = Form(default=""),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    service: OrdinateurService = Depends(_obtenir_service),
):
    """Enregistre un evenement depuis le formulaire web (admin uniquement)."""
    message_succes = None
    message_erreur = None

    utilisateur = getattr(request.state, "utilisateur", None)
    if not peut_enregistrer_evenement(utilisateur):
        message_erreur = "acces_refuse"
    else:
        try:
            donnees = EvenementCreate(
                date_evenement=date.fromisoformat(date_evenement),
                type_evenement=TypeEvenement(type_evenement),
                commentaire=commentaire.strip() or None,
            )
            service.enregistrer_evenement(ordinateur_id, donnees)
            message_succes = "evenement_enregistre"
        except ValidationError:
            message_erreur = "erreur_evenement"
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "erreur_evenement"
            message_erreur = detail
        except ValueError:
            message_erreur = "erreur_evenement"

    filtres = _params_filtres(recherche or None, statut or None)
    ordinateurs = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "ordinateurs/partials/liste_cartes.html",
        _contexte_liste(
            request,
            ordinateurs,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )
