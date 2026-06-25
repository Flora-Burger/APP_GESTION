"""Abstraction de stockage de fichiers (local ou Vercel Blob)."""

import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import RACINE_PROJET, obtenir_parametres

EXTENSIONS_AUTORISEES = {".jpg", ".jpeg", ".png", ".webp"}
TAILLE_MAX_OCTETS = 5 * 1024 * 1024
MIME_PAR_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
HOTE_BLOB_VERCEL = "blob.vercel-storage.com"


async def _lire_fichier_upload(fichier: UploadFile) -> tuple[bytes, str]:
    """Valide et lit le contenu d'un fichier upload."""
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

    return contenu, extension


class StockageFichiers:
    """Stockage local (dev) ou Vercel Blob (production)."""

    def __init__(self, sous_dossier: str):
        self.sous_dossier = sous_dossier
        self.prefixe_local = f"/static/uploads/{sous_dossier}/"
        self.dossier_local = RACINE_PROJET / "static" / "uploads" / sous_dossier

    def _assurer_dossier_local(self) -> None:
        self.dossier_local.mkdir(parents=True, exist_ok=True)

    def est_photo_geree(self, url: str) -> bool:
        """Indique si l'URL correspond a un fichier que l'app peut supprimer."""
        if not url:
            return False
        if url.startswith(self.prefixe_local):
            return True
        return HOTE_BLOB_VERCEL in url

    def chemin_fichier_local_depuis_url(self, url: str) -> Path | None:
        """Retourne le chemin disque d'une photo locale."""
        if not url.startswith(self.prefixe_local):
            return None
        relatif = url.removeprefix("/static/")
        return RACINE_PROJET / "static" / relatif

    async def enregistrer(self, fichier: UploadFile) -> str:
        """Enregistre une photo et retourne son URL publique."""
        contenu, extension = await _lire_fichier_upload(fichier)
        parametres = obtenir_parametres()

        if parametres.utilise_blob():
            return await self._enregistrer_blob(contenu, extension, parametres)

        return self._enregistrer_local(contenu, extension)

    def supprimer(self, url: str) -> None:
        """Supprime une photo locale ou sur Vercel Blob."""
        if not self.est_photo_geree(url):
            return

        if url.startswith(self.prefixe_local):
            chemin = self.chemin_fichier_local_depuis_url(url)
            if chemin and chemin.is_file():
                chemin.unlink()
            return

        parametres = obtenir_parametres()
        if parametres.utilise_blob() and HOTE_BLOB_VERCEL in url:
            self._supprimer_blob(url, parametres)

    def _enregistrer_local(self, contenu: bytes, extension: str) -> str:
        self._assurer_dossier_local()
        nom_fichier = f"{uuid.uuid4().hex}{extension}"
        chemin = self.dossier_local / nom_fichier
        chemin.write_bytes(contenu)
        return f"{self.prefixe_local}{nom_fichier}"

    async def _enregistrer_blob(
        self,
        contenu: bytes,
        extension: str,
        parametres,
    ) -> str:
        nom_fichier = f"{uuid.uuid4().hex}{extension}"
        pathname = f"{self.sous_dossier}/{nom_fichier}"
        content_type = MIME_PAR_EXTENSION[extension]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"https://{HOTE_BLOB_VERCEL}/{pathname}",
                content=contenu,
                headers={
                    "Authorization": f"Bearer {parametres.blob_read_write_token}",
                    "Content-Type": content_type,
                    "x-api-version": "7",
                },
            )
            response.raise_for_status()
            data = response.json()

        url = data.get("url")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="erreur_stockage_blob",
            )
        return url

    def _supprimer_blob(self, url: str, parametres) -> None:
        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                "DELETE",
                f"https://{HOTE_BLOB_VERCEL}",
                json={"url": url},
                headers={
                    "Authorization": f"Bearer {parametres.blob_read_write_token}",
                },
            )
            if response.status_code not in (200, 404):
                response.raise_for_status()
