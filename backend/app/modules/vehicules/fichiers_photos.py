"""Gestion des fichiers photo uploades pour les vehicules."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import RACINE_PROJET

DOSSIER_UPLOADS = RACINE_PROJET / "static" / "uploads" / "vehicules"
PREFIXE_URL_LOCALE = "/static/uploads/vehicules/"
EXTENSIONS_AUTORISEES = {".jpg", ".jpeg", ".png", ".webp"}
TAILLE_MAX_OCTETS = 5 * 1024 * 1024


def _assurer_dossier() -> None:
    """Cree le dossier d'upload si necessaire."""
    DOSSIER_UPLOADS.mkdir(parents=True, exist_ok=True)


def est_photo_locale(url: str) -> bool:
    """Indique si l'URL pointe vers un fichier local upload."""
    return bool(url) and url.startswith(PREFIXE_URL_LOCALE)


def chemin_fichier_depuis_url(url: str) -> Path | None:
    """Retourne le chemin disque d'une photo locale."""
    if not est_photo_locale(url):
        return None
    relatif = url.removeprefix("/static/")
    return RACINE_PROJET / "static" / relatif


async def enregistrer_photo_vehicule(fichier: UploadFile) -> str:
    """Enregistre une photo uploadée et retourne son URL publique."""
    if not fichier.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="photo_invalide",
        )

    extension = Path(fichier.filename).suffix.lower()
    if extension not in EXTENSIONS_AUTORISEES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="photo_format_invalide",
        )

    contenu = await fichier.read()
    if not contenu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="photo_invalide",
        )
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="photo_trop_volumineuse",
        )

    _assurer_dossier()
    nom_fichier = f"{uuid.uuid4().hex}{extension}"
    chemin = DOSSIER_UPLOADS / nom_fichier
    chemin.write_bytes(contenu)

    return f"{PREFIXE_URL_LOCALE}{nom_fichier}"


def supprimer_photo_locale(url: str) -> None:
    """Supprime un fichier photo local s'il existe."""
    chemin = chemin_fichier_depuis_url(url)
    if chemin and chemin.is_file():
        chemin.unlink()
