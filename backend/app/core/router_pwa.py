"""Manifeste et service worker pour l'installation PWA."""

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import RACINE_PROJET, obtenir_parametres

router = APIRouter(tags=["pwa"])


@router.get("/manifest.webmanifest")
def manifest_web():
    """Manifeste d'application web progressive."""
    parametres = obtenir_parametres()
    return JSONResponse(
        {
            "name": f"{parametres.nom_entreprise} - Gestion",
            "short_name": "FLORA",
            "description": "Gestion del parque de recursos corporativo",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "orientation": "portrait-primary",
            "background_color": "#f4f8fc",
            "theme_color": "#0f3d7a",
            "lang": "es",
            "icons": [
                {
                    "src": "/static/pwa/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": "/static/pwa/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
    )


@router.get("/sw.js")
def service_worker():
    """Service worker racine (scope /)."""
    return FileResponse(
        RACINE_PROJET / "static" / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )
