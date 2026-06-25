"""Routes web d'administration des vehicules (admin uniquement)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.admin_web import verifier_admin_web
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.vehicules.schemas import VehiculeCreateAdmin, VehiculeUpdateAdmin
from backend.app.modules.vehicules.service import VehiculeService

router = APIRouter(tags=["admin-vehicules"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> VehiculeService:
    return VehiculeService(session)


@router.get("/admin/vehicules", response_class=HTMLResponse)
def page_admin_vehicules(
    request: Request,
    recherche: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    """Liste et creation de vehicules."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    vehicules = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/vehicules.html",
        contexte_template(
            request,
            vehicules=vehicules,
            filtres_actifs={"recherche": recherche or ""},
            message=message,
            erreur=erreur,
        ),
    )


@router.get("/admin/vehicules/partials/liste", response_class=HTMLResponse)
def partial_liste_admin_vehicules(
    request: Request,
    recherche: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Fragment HTMX de la liste admin des vehicules."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    vehicules = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/partials/vehicules_table.html",
        contexte_template(request, vehicules=vehicules),
    )


@router.post("/admin/vehicules")
async def creer_vehicule_admin(
    request: Request,
    matricule: str = Form(...),
    modele: str = Form(...),
    kilometrage_actuel: str = Form(...),
    photo: UploadFile | None = File(None),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Cree un vehicule (matricule + modele + kilometrage + photo optionnelle)."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        km = int(kilometrage_actuel.strip())
        if km < 0:
            raise ValueError
        donnees = VehiculeCreateAdmin(
            matricule=matricule,
            modele=modele,
            kilometrage_actuel=km,
        )
        await service.creer_admin(donnees, photo)
        return RedirectResponse(url="/admin/vehicules?message=vehicule_cree", status_code=303)
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/admin/vehicules?erreur=erreur_kilometrage_invalide",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_creation_vehicule"
        erreurs_connues = {
            "matricule_existant",
            "photo_invalide",
            "photo_format_invalide",
            "photo_trop_volumineuse",
            "erreur_kilometrage_invalide",
            "erreur_stockage_blob",
        }
        erreur = detail if detail in erreurs_connues else "erreur_creation_vehicule"
        return RedirectResponse(url=f"/admin/vehicules?erreur={erreur}", status_code=303)


@router.get("/admin/vehicules/{vehicule_id}/modifier", response_class=HTMLResponse)
def page_modifier_vehicule(
    request: Request,
    vehicule_id: int,
    service: VehiculeService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    """Formulaire de modification d'un vehicule."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        vehicule = service.obtenir_detail(vehicule_id)
    except HTTPException:
        return RedirectResponse(url="/admin/vehicules?erreur=vehicule_introuvable", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/vehicule_modifier.html",
        contexte_template(
            request,
            vehicule=vehicule,
            message=message,
            erreur=erreur,
        ),
    )


@router.post("/admin/vehicules/{vehicule_id}/modifier")
async def modifier_vehicule_admin(
    request: Request,
    vehicule_id: int,
    matricule: str = Form(...),
    modele: str = Form(...),
    photo: UploadFile | None = File(None),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Met a jour matricule, modele et photo."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        donnees = VehiculeUpdateAdmin(matricule=matricule, modele=modele)
        await service.modifier_admin(vehicule_id, donnees, photo)
        return RedirectResponse(
            url=f"/admin/vehicules/{vehicule_id}/modifier?message=vehicule_modifie",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_modification_vehicule"
        erreurs_connues = {
            "matricule_existant",
            "vehicule_introuvable",
            "photo_invalide",
            "photo_format_invalide",
            "photo_trop_volumineuse",
            "erreur_stockage_blob",
        }
        erreur = detail if detail in erreurs_connues else "erreur_modification_vehicule"
        return RedirectResponse(
            url=f"/admin/vehicules/{vehicule_id}/modifier?erreur={erreur}",
            status_code=303,
        )


@router.post("/admin/vehicules/{vehicule_id}/supprimer")
def supprimer_vehicule_admin(
    request: Request,
    vehicule_id: int,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Supprime un vehicule."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.supprimer_admin(vehicule_id)
        return RedirectResponse(url="/admin/vehicules?message=vehicule_supprime", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_suppression_vehicule"
        erreur = detail if detail == "vehicule_introuvable" else "erreur_suppression_vehicule"
        return RedirectResponse(url=f"/admin/vehicules?erreur={erreur}", status_code=303)
