"""Routes web pour la page d'accueil."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.accueil.service import AccueilService
from backend.app.modules.auth.affichage import doit_rediriger_accueil_vers_vehicules
from backend.app.modules.base.registre_modules import obtenir_tous_modules
from backend.app.modules.imprimantes.service import ImprimanteService
from backend.app.modules.ordinateurs.service import OrdinateurService
from backend.app.modules.vehicules.service import VehiculeService

router = APIRouter(tags=["accueil"])


@router.get("/", response_class=HTMLResponse)
def page_accueil(request: Request, session: Session = Depends(obtenir_session)):
    """Page d'accueil avec tableau de bord du parc materiel."""
    utilisateur = getattr(request.state, "utilisateur", None)
    if doit_rediriger_accueil_vers_vehicules(utilisateur, request):
        return RedirectResponse(url="/vehicules", status_code=303)

    modules = obtenir_tous_modules()
    tableau_bord = AccueilService(session).obtenir_tableau_bord()
    return templates.TemplateResponse(
        request,
        "accueil.html",
        contexte_template(request, modules=modules, tableau_bord=tableau_bord),
    )


@router.get("/partials/recherche", response_class=HTMLResponse)
def partial_recherche(
    request: Request,
    q: str = Query(default=""),
    session: Session = Depends(obtenir_session),
):
    """Fragment HTMX des resultats de recherche globale."""
    service_vehicules = VehiculeService(session)
    service_imprimantes = ImprimanteService(session)
    resultats = service_vehicules.rechercher_global(q)
    resultats.extend(service_imprimantes.rechercher_global(q))
    resultats.extend(OrdinateurService(session).rechercher_global(q))

    return templates.TemplateResponse(
        request,
        "partials/recherche_resultats.html",
        contexte_template(request, resultats=resultats, terme=q),
    )
