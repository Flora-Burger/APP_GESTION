"""Utilitaires partages pour les pages d'administration web."""

from fastapi import Request
from fastapi.responses import RedirectResponse

from backend.app.modules.auth.schemas import RoleUtilisateur


def verifier_admin_web(request: Request) -> RedirectResponse | None:
    """Redirige si l'utilisateur n'est pas administrateur."""
    utilisateur = getattr(request.state, "utilisateur", None)
    if utilisateur is None or utilisateur.role != RoleUtilisateur.ADMIN.value:
        return RedirectResponse(url="/", status_code=303)
    return None
