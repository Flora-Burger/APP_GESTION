"""Point d'entree de l'application FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from backend.app.core.auth_middleware import AuthMiddleware
from backend.app.core.config import RACINE_PROJET, obtenir_parametres
from backend.app.core.database import SessionLocal
from backend.app.core.router_pwa import router as router_pwa
from backend.app.modules.accueil.router_web import router as router_accueil
from backend.app.modules.auth.router_admin import router as router_admin
from backend.app.modules.auth.router_web import router as router_auth
from backend.app.modules.auth.service import AuthService
from backend.app.modules.imprimantes.router_admin import router as router_admin_imprimantes
from backend.app.modules.imprimantes.router_api import router as router_api_imprimantes
from backend.app.modules.imprimantes.router_web import router as router_web_imprimantes
from backend.app.modules.ordinateurs.router_admin import router as router_admin_ordinateurs
from backend.app.modules.ordinateurs.router_api import router as router_api_ordinateurs
from backend.app.modules.ordinateurs.router_web import router as router_web_ordinateurs
from backend.app.modules.vehicules.router_admin import router as router_admin_vehicules
from backend.app.modules.vehicules.router_api import router as router_api_vehicules
from backend.app.modules.vehicules.router_web import router as router_web_vehicules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application."""
    parametres = obtenir_parametres()
    logging.getLogger(__name__).info(
        "Demarrage de l'application %s", parametres.nom_entreprise
    )

    session = SessionLocal()
    try:
        AuthService(session).initialiser_admin_par_defaut()
    finally:
        session.close()

    yield


app = FastAPI(
    title="FLORA - Gestion des ressources",
    description="API de gestion des ressources materielles de l'entreprise",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)


@app.exception_handler(RequestValidationError)
async def erreur_validation_formulaire_web(request: Request, exc: RequestValidationError):
    """Redirige les erreurs de formulaire web vers la page admin utilisateurs."""
    chemin = request.url.path
    if request.method == "POST" and chemin == "/admin/users":
        return RedirectResponse(url="/admin/users?erreur=erreur_creation", status_code=303)
    if request.method == "POST" and chemin.startswith("/admin/users/") and chemin.endswith("/modifier"):
        parties = chemin.strip("/").split("/")
        utilisateur_id = parties[2] if len(parties) >= 3 else ""
        return RedirectResponse(
            url=f"/admin/users?erreur=erreur_modification&modifier_id={utilisateur_id}",
            status_code=303,
        )
    raise exc


app.mount("/static", StaticFiles(directory=str(RACINE_PROJET / "static")), name="static")

# PWA (manifeste et service worker publics)
app.include_router(router_pwa)

# Auth (login public via middleware)
app.include_router(router_auth)

# Routes web protegees
app.include_router(router_accueil)
app.include_router(router_web_vehicules)
app.include_router(router_web_imprimantes)
app.include_router(router_web_ordinateurs)
app.include_router(router_admin)
app.include_router(router_admin_vehicules)
app.include_router(router_admin_imprimantes)
app.include_router(router_admin_ordinateurs)

# Routes API REST protegees
app.include_router(router_api_vehicules, prefix="/api/v1")
app.include_router(router_api_imprimantes, prefix="/api/v1")
app.include_router(router_api_ordinateurs, prefix="/api/v1")
