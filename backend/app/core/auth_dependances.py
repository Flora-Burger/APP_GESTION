"""Dependances d'authentification pour les routes."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import obtenir_parametres
from backend.app.core.database import obtenir_session
from backend.app.core.securite import decoder_token
from backend.app.modules.auth.modeles import Utilisateur
from backend.app.modules.auth.schemas import RoleUtilisateur
from backend.app.modules.auth.service import AuthService


def _extraire_token(request: Request) -> str | None:
    """Extrait le token JWT du cookie."""
    parametres = obtenir_parametres()
    return request.cookies.get(parametres.cookie_auth_nom)


def obtenir_utilisateur_optionnel(
    request: Request,
    session: Session = Depends(obtenir_session),
) -> Utilisateur | None:
    """Retourne l'utilisateur courant ou None."""
    token = _extraire_token(request)
    if not token:
        return None

    payload = decoder_token(token)
    if payload is None:
        return None

    service = AuthService(session)
    try:
        return service.obtenir_utilisateur_actif(payload.uid)
    except HTTPException:
        return None


def obtenir_utilisateur_connecte(
    request: Request,
    session: Session = Depends(obtenir_session),
) -> Utilisateur:
    """Exige un utilisateur authentifie (API)."""
    utilisateur = obtenir_utilisateur_optionnel(request, session)
    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="non_authentifie",
        )
    return utilisateur


def exiger_admin(
    utilisateur: Utilisateur = Depends(obtenir_utilisateur_connecte),
) -> Utilisateur:
    """Exige un administrateur connecte."""
    if utilisateur.role != RoleUtilisateur.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="acces_refuse",
        )
    return utilisateur
