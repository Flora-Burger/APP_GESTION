"""Routes web d'administration des imprimantes (admin uniquement)."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.admin_web import verifier_admin_web
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.imprimantes.schemas import ImprimanteCreate, ImprimanteUpdate, StatutImprimante
from backend.app.modules.imprimantes.service import ImprimanteService

router = APIRouter(tags=["admin-imprimantes"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> ImprimanteService:
    return ImprimanteService(session)


def _parse_date(valeur: str) -> date | None:
    if not valeur or not valeur.strip():
        return None
    return date.fromisoformat(valeur.strip())


@router.get("/admin/imprimantes", response_class=HTMLResponse)
def page_admin_imprimantes(
    request: Request,
    recherche: str | None = None,
    service: ImprimanteService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    """Liste et creation d'imprimantes."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    imprimantes = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/imprimantes.html",
        contexte_template(
            request,
            imprimantes=imprimantes,
            filtres_actifs={"recherche": recherche or ""},
            message=message,
            erreur=erreur,
            statuts=StatutImprimante,
        ),
    )


@router.get("/admin/imprimantes/partials/liste", response_class=HTMLResponse)
def partial_liste_admin_imprimantes(
    request: Request,
    recherche: str | None = None,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Fragment HTMX de la liste admin des imprimantes."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    imprimantes = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/partials/imprimantes_table.html",
        contexte_template(request, imprimantes=imprimantes, statuts=StatutImprimante),
    )


@router.post("/admin/imprimantes")
def creer_imprimante_admin(
    request: Request,
    nom: str = Form(...),
    modele: str = Form(...),
    localisation: str = Form(...),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Cree une imprimante."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        donnees = ImprimanteCreate(
            nom=nom,
            modele=modele,
            localisation=localisation,
            compteur_initial=0,
        )
        service.creer(donnees)
        return RedirectResponse(url="/admin/imprimantes?message=imprimante_creee", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_creation_imprimante"
        erreur = detail if detail == "nom_existant" else "erreur_creation_imprimante"
        return RedirectResponse(url=f"/admin/imprimantes?erreur={erreur}", status_code=303)


@router.get("/admin/imprimantes/{imprimante_id}/modifier", response_class=HTMLResponse)
def page_modifier_imprimante(
    request: Request,
    imprimante_id: int,
    service: ImprimanteService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    """Formulaire de modification."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        imprimante = service.obtenir_detail(imprimante_id)
    except HTTPException:
        return RedirectResponse(url="/admin/imprimantes?erreur=imprimante_introuvable", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/imprimante_modifier.html",
        contexte_template(
            request,
            imprimante=imprimante,
            message=message,
            erreur=erreur,
            statuts=StatutImprimante,
        ),
    )


@router.post("/admin/imprimantes/{imprimante_id}/modifier")
async def modifier_imprimante_admin(
    request: Request,
    imprimante_id: int,
    nom: str = Form(...),
    modele: str = Form(...),
    localisation: str = Form(...),
    fecha_compra: str = Form(default=""),
    tipo_tinta: str = Form(default=""),
    facture: UploadFile | None = File(default=None),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Met a jour les donnees maitres."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        donnees = ImprimanteUpdate(
            nom=nom,
            modele=modele,
            localisation=localisation,
            fecha_compra=_parse_date(fecha_compra),
            tipo_tinta=tipo_tinta or None,
        )
        await service.modifier_avec_facture(imprimante_id, donnees, facture)
        return RedirectResponse(
            url=f"/admin/imprimantes/{imprimante_id}/modifier?message=imprimante_modifiee",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_modification_imprimante"
        erreurs_connues = {"nom_existant", "imprimante_introuvable", "fichier_invalide", "fichier_trop_volumineux"}
        erreur = detail if detail in erreurs_connues else "erreur_modification_imprimante"
        return RedirectResponse(
            url=f"/admin/imprimantes/{imprimante_id}/modifier?erreur={erreur}",
            status_code=303,
        )


@router.post("/admin/imprimantes/{imprimante_id}/statut")
def modifier_statut_imprimante_admin(
    request: Request,
    imprimante_id: int,
    statut: str = Form(...),
    retour: str = Form(default=""),
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Met a jour le statut directement (admin)."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.modifier_statut(imprimante_id, StatutImprimante(statut))
        if retour == "liste":
            return RedirectResponse(url="/imprimantes?message=statut_imprimante_modifie", status_code=303)
        return RedirectResponse(
            url=f"/admin/imprimantes/{imprimante_id}/modifier?message=statut_imprimante_modifie",
            status_code=303,
        )
    except (ValueError, HTTPException):
        return RedirectResponse(
            url=f"/admin/imprimantes/{imprimante_id}/modifier?erreur=erreur_modification_imprimante",
            status_code=303,
        )


@router.post("/admin/imprimantes/{imprimante_id}/supprimer")
def supprimer_imprimante_admin(
    request: Request,
    imprimante_id: int,
    service: ImprimanteService = Depends(_obtenir_service),
):
    """Supprime une imprimante."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.supprimer(imprimante_id)
        return RedirectResponse(url="/admin/imprimantes?message=imprimante_supprimee", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_suppression_imprimante"
        erreur = detail if detail == "imprimante_introuvable" else "erreur_suppression_imprimante"
        return RedirectResponse(url=f"/admin/imprimantes?erreur={erreur}", status_code=303)
