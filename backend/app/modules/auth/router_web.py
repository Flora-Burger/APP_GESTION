"""Routes web d'authentification (login / logout)."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import obtenir_parametres
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.affichage import obtenir_destination_apres_connexion
from backend.app.modules.auth.service import AuthService

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
def page_login(request: Request, erreur: str | None = None):
    """Page de connexion (publique)."""
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        contexte_template(request, erreur=erreur),
    )


@router.post("/login")
def traiter_login(
    request: Request,
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    session: Session = Depends(obtenir_session),
):
    """Traite la connexion et pose le cookie JWT."""
    parametres = obtenir_parametres()
    service = AuthService(session)
    message_erreur = None

    try:
        utilisateur, token = service.authentifier(email, mot_de_passe)
    except HTTPException as exc:
        if exc.detail == "compte_desactive":
            message_erreur = "compte_desactive"
        elif exc.detail == "identifiants_invalides":
            message_erreur = "identifiants_invalides"
        elif exc.detail == "identifiant_invalide":
            message_erreur = "identifiant_invalide"
        else:
            message_erreur = "erreur_connexion"

        return templates.TemplateResponse(
            request,
            "auth/login.html",
            contexte_template(request, erreur=message_erreur),
            status_code=401,
        )

    destination = obtenir_destination_apres_connexion(utilisateur, request)
    reponse = RedirectResponse(url=destination, status_code=303)
    reponse.set_cookie(
        key=parametres.cookie_auth_nom,
        value=token,
        httponly=True,
        samesite="lax",
        secure=parametres.cookie_secure,
        max_age=parametres.jwt_expiration_minutes * 60,
    )
    return reponse


@router.get("/logout")
def deconnexion():
    """Deconnexion et suppression du cookie."""
    parametres = obtenir_parametres()
    reponse = RedirectResponse(url="/login", status_code=303)
    reponse.delete_cookie(parametres.cookie_auth_nom)
    return reponse


@router.get("/contacts", response_class=HTMLResponse)
def page_contacts(request: Request, session: Session = Depends(obtenir_session)):
    """Liste des contacts de l'entreprise (utilisateurs actifs)."""
    utilisateur = getattr(request.state, "utilisateur", None)
    if utilisateur is None:
        return RedirectResponse(url="/login", status_code=303)

    service = AuthService(session)
    contacts_groupes = service.lister_contacts_entreprise()

    return templates.TemplateResponse(
        request,
        "contacts/liste.html",
        contexte_template(
            request,
            contacts_admins=contacts_groupes["admins"],
            contacts_utilisateurs=contacts_groupes["utilisateurs"],
        ),
    )
