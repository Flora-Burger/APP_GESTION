"""Routes web d'administration des utilisateurs (admin uniquement)."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.admin_web import verifier_admin_web
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.affichage import (
    extraire_nom_formulaire,
    parser_role_utilisateur,
    preparer_utilisateurs_affichage,
)
from backend.app.modules.auth.schemas import UtilisateurCreate, UtilisateurUpdate
from backend.app.modules.auth.service import AuthService

router = APIRouter(tags=["admin"])
logger = logging.getLogger(__name__)


def _erreur_validation_formulaire(exc: ValidationError) -> str:
    """Determine le code d'erreur a afficher apres une ValidationError."""
    for erreur in exc.errors():
        champs = erreur.get("loc", ())
        if "email" in champs:
            return "identifiant_invalide"
        if "nom" in champs:
            return "nom_obligatoire"
    return "erreur_creation"


@router.get("/admin/users", response_class=HTMLResponse)
def page_utilisateurs(
    request: Request,
    session: Session = Depends(obtenir_session),
    message: str | None = None,
    erreur: str | None = None,
    modifier_id: int | None = None,
):
    """Liste, creation et gestion des comptes utilisateurs."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    service = AuthService(session)
    utilisateurs = preparer_utilisateurs_affichage(service.lister_utilisateurs())

    return templates.TemplateResponse(
        request,
        "admin/users.html",
        contexte_template(
            request,
            utilisateurs=utilisateurs,
            message=message,
            erreur=erreur,
            modifier_id=modifier_id,
        ),
    )


@router.post("/admin/users")
def creer_utilisateur(
    request: Request,
    email: str = Form(...),
    nom: str = Form(default=""),
    prenom: str = Form(default=""),
    nom_famille: str = Form(default=""),
    telefono: str = Form(default=""),
    correo: str = Form(default=""),
    mot_de_passe: str = Form(...),
    role: str = Form(...),
    session: Session = Depends(obtenir_session),
):
    """Cree un nouveau compte utilisateur ou admin."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    nom_normalise = extraire_nom_formulaire(nom=nom, prenom=prenom, nom_famille=nom_famille)
    if not nom_normalise:
        return RedirectResponse(url="/admin/users?erreur=nom_obligatoire", status_code=303)

    service = AuthService(session)
    try:
        role_enum = parser_role_utilisateur(role)
        donnees = UtilisateurCreate(
            email=email,
            mot_de_passe=mot_de_passe,
            nom=nom_normalise,
            telefono=telefono or None,
            correo=correo or None,
            role=role_enum,
        )
        service.creer_utilisateur(donnees)
        return RedirectResponse(url="/admin/users?message=compte_cree", status_code=303)
    except ValidationError as exc:
        erreur = _erreur_validation_formulaire(exc)
        return RedirectResponse(url=f"/admin/users?erreur={erreur}", status_code=303)
    except ValueError:
        return RedirectResponse(url="/admin/users?erreur=erreur_creation", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_creation"
        erreur = "email_existant" if detail == "email_existant" else "erreur_creation"
        return RedirectResponse(url=f"/admin/users?erreur={erreur}", status_code=303)


@router.post("/admin/users/{utilisateur_id}/modifier")
def modifier_utilisateur(
    request: Request,
    utilisateur_id: int,
    email: str = Form(...),
    nom: str = Form(default=""),
    prenom: str = Form(default=""),
    nom_famille: str = Form(default=""),
    telefono: str = Form(default=""),
    correo: str = Form(default=""),
    mot_de_passe: str = Form(default=""),
    role: str = Form(...),
    session: Session = Depends(obtenir_session),
):
    """Met a jour email, nom, mot de passe et role."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    nom_normalise = extraire_nom_formulaire(nom=nom, prenom=prenom, nom_famille=nom_famille)
    if not nom_normalise:
        return RedirectResponse(
            url=f"/admin/users?erreur=nom_obligatoire&modifier_id={utilisateur_id}",
            status_code=303,
        )

    admin_id = request.state.utilisateur.id
    service = AuthService(session)
    try:
        role_enum = parser_role_utilisateur(role)
        donnees = UtilisateurUpdate(
            email=email,
            nom=nom_normalise,
            telefono=telefono or None,
            correo=correo or None,
            mot_de_passe=mot_de_passe or None,
            role=role_enum,
        )
        service.modifier_utilisateur(utilisateur_id, donnees, admin_id)
        return RedirectResponse(url="/admin/users?message=compte_modifie", status_code=303)
    except ValidationError as exc:
        erreur = _erreur_validation_formulaire(exc)
        if erreur == "erreur_creation":
            erreur = "erreur_modification"
        return RedirectResponse(
            url=f"/admin/users?erreur={erreur}&modifier_id={utilisateur_id}",
            status_code=303,
        )
    except ValueError:
        return RedirectResponse(
            url=f"/admin/users?erreur=erreur_modification&modifier_id={utilisateur_id}",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_modification"
        erreurs_connues = {
            "email_existant",
            "introuvable",
            "auto_desactivation_interdite",
            "dernier_admin",
        }
        erreur = detail if detail in erreurs_connues else "erreur_modification"
        return RedirectResponse(
            url=f"/admin/users?erreur={erreur}&modifier_id={utilisateur_id}",
            status_code=303,
        )
    except Exception:
        logger.exception("Erreur inattendue lors de la modification du compte %s", utilisateur_id)
        return RedirectResponse(
            url=f"/admin/users?erreur=erreur_modification&modifier_id={utilisateur_id}",
            status_code=303,
        )


@router.post("/admin/users/{utilisateur_id}/toggle")
def basculer_utilisateur(
    request: Request,
    utilisateur_id: int,
    session: Session = Depends(obtenir_session),
):
    """Active ou desactive un compte."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    admin_id = request.state.utilisateur.id
    service = AuthService(session)
    try:
        service.basculer_actif(utilisateur_id, admin_id)
        return RedirectResponse(url="/admin/users?message=statut_modifie", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur"
        return RedirectResponse(url=f"/admin/users?erreur={detail}", status_code=303)


@router.post("/admin/users/{utilisateur_id}/supprimer")
def supprimer_utilisateur(
    request: Request,
    utilisateur_id: int,
    session: Session = Depends(obtenir_session),
):
    """Supprime un compte."""
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    admin_id = request.state.utilisateur.id
    service = AuthService(session)
    try:
        service.supprimer_utilisateur(utilisateur_id, admin_id)
        return RedirectResponse(url="/admin/users?message=compte_supprime", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur"
        return RedirectResponse(url=f"/admin/users?erreur={detail}", status_code=303)
