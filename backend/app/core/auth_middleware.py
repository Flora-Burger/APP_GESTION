"""Middleware de protection des routes par authentification."""

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from backend.app.core.config import obtenir_parametres
from backend.app.core.database import SessionLocal
from backend.app.core.securite import decoder_token
from backend.app.modules.auth.service import AuthService

CHEMINS_PUBLICS = (
    "/login",
    "/static",
    "/manifest.webmanifest",
    "/sw.js",
    "/docs",
    "/redoc",
    "/openapi.json",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Redirige vers /login si non authentifie (web) ou 401 (API)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        chemin = request.url.path

        if self._est_public(chemin):
            return await call_next(request)

        parametres = obtenir_parametres()
        token = request.cookies.get(parametres.cookie_auth_nom)

        if not token:
            return self._refuser(request)

        payload = decoder_token(token)
        if payload is None:
            reponse = self._refuser(request)
            reponse.delete_cookie(parametres.cookie_auth_nom)
            return reponse

        session = SessionLocal()
        try:
            service = AuthService(session)
            utilisateur = service.obtenir_utilisateur_actif(payload.uid)
        except HTTPException:
            reponse = self._refuser(request)
            reponse.delete_cookie(parametres.cookie_auth_nom)
            return reponse
        finally:
            session.expunge(utilisateur)
            session.close()

        request.state.utilisateur = utilisateur
        return await call_next(request)

    @staticmethod
    def _est_public(chemin: str) -> bool:
        """Verifie si le chemin est accessible sans authentification."""
        return any(chemin == p or chemin.startswith(p + "/") for p in CHEMINS_PUBLICS)

    @staticmethod
    def _refuser(request: Request) -> Response:
        """Reponse 401 API ou redirection login."""
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=401,
                content={"detail": "non_authentifie"},
            )
        return RedirectResponse(url="/login", status_code=303)
