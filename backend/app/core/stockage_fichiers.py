"""Abstraction de stockage de fichiers (local ou Vercel Blob)."""

import logging
import os
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import RACINE_PROJET, obtenir_parametres

logger = logging.getLogger(__name__)

EXTENSIONS_IMAGE = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSIONS_DOCUMENT = EXTENSIONS_IMAGE | {".pdf"}
TAILLE_MAX_OCTETS = 5 * 1024 * 1024
MIME_PAR_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}
URL_API_BLOB = "https://vercel.com/api/blob"
VERSION_API_BLOB = "12"
SUFFIXES_URL_BLOB = (
    "blob.vercel-storage.com",
    ".public.blob.vercel-storage.com",
    ".private.blob.vercel-storage.com",
)


async def _lire_fichier_upload(
    fichier: UploadFile,
    extensions_autorisees: set[str] | None = None,
) -> tuple[bytes, str]:
    """Valide et lit le contenu d'un fichier upload."""
    if extensions_autorisees is None:
        extensions_autorisees = EXTENSIONS_IMAGE

    if not fichier.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fichier_invalide",
        )

    extension = Path(fichier.filename).suffix.lower()
    if extension not in extensions_autorisees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fichier_format_invalide",
        )

    contenu = await fichier.read()
    if not contenu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fichier_invalide",
        )
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fichier_trop_volumineux",
        )

    return contenu, extension


def _normaliser_store_id(store_id: str) -> str:
    return store_id.removeprefix("store_")


def _parser_store_id_depuis_token(token: str) -> str | None:
    """Extrait l'id du store depuis un token vercel_blob_rw_{storeId}_..."""
    parties = token.split("_")
    if len(parties) >= 4 and parties[:3] == ["vercel", "blob", "rw"]:
        return parties[3]
    return None


def _obtenir_credentials_blob() -> tuple[str, str] | None:
    """Retourne (token, store_id) pour l'API Vercel Blob."""
    parametres = obtenir_parametres()

    if parametres.blob_read_write_token:
        store_id = _parser_store_id_depuis_token(parametres.blob_read_write_token)
        if store_id:
            return parametres.blob_read_write_token, store_id

    oidc = os.getenv("VERCEL_OIDC_TOKEN")
    store_id_env = os.getenv("BLOB_STORE_ID")
    if oidc and store_id_env:
        return oidc, _normaliser_store_id(store_id_env)

    return None


def _entetes_blob_api(token: str, store_id: str, **extra: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "x-api-version": VERSION_API_BLOB,
        "x-vercel-blob-store-id": store_id,
        **extra,
    }


def _est_url_blob(url: str) -> bool:
    return bool(url) and any(suffixe in url for suffixe in SUFFIXES_URL_BLOB)


class StockageFichiers:
    """Stockage local (dev) ou Vercel Blob (production)."""

    def __init__(self, sous_dossier: str):
        self.sous_dossier = sous_dossier
        self.prefixe_local = f"/static/uploads/{sous_dossier}/"
        self.dossier_local = RACINE_PROJET / "static" / "uploads" / sous_dossier

    def _assurer_dossier_local(self) -> None:
        self.dossier_local.mkdir(parents=True, exist_ok=True)

    def est_fichier_gere(self, url: str) -> bool:
        """Indique si l'URL correspond a un fichier que l'app peut supprimer."""
        if not url:
            return False
        if url.startswith(self.prefixe_local):
            return True
        return _est_url_blob(url)

    est_photo_geree = est_fichier_gere

    def chemin_fichier_local_depuis_url(self, url: str) -> Path | None:
        """Retourne le chemin disque d'une photo locale."""
        if not url.startswith(self.prefixe_local):
            return None
        relatif = url.removeprefix("/static/")
        return RACINE_PROJET / "static" / relatif

    async def enregistrer(self, fichier: UploadFile) -> str:
        """Enregistre une image et retourne son URL publique."""
        return await self._enregistrer_fichier(fichier, EXTENSIONS_IMAGE)

    async def enregistrer_document(self, fichier: UploadFile) -> str:
        """Enregistre une image ou un PDF et retourne son URL publique."""
        return await self._enregistrer_fichier(fichier, EXTENSIONS_DOCUMENT)

    async def _enregistrer_fichier(
        self,
        fichier: UploadFile,
        extensions_autorisees: set[str],
    ) -> str:
        contenu, extension = await _lire_fichier_upload(fichier, extensions_autorisees)
        parametres = obtenir_parametres()

        if parametres.utilise_blob():
            return await self._enregistrer_blob(contenu, extension)

        if parametres.est_vercel():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="erreur_stockage_blob",
            )

        return self._enregistrer_local(contenu, extension)

    def supprimer(self, url: str) -> None:
        """Supprime un fichier local ou sur Vercel Blob."""
        if not self.est_fichier_gere(url):
            return

        if url.startswith(self.prefixe_local):
            chemin = self.chemin_fichier_local_depuis_url(url)
            if chemin and chemin.is_file():
                chemin.unlink()
            return

        if _est_url_blob(url) and obtenir_parametres().utilise_blob():
            self._supprimer_blob(url)

    def _enregistrer_local(self, contenu: bytes, extension: str) -> str:
        self._assurer_dossier_local()
        nom_fichier = f"{uuid.uuid4().hex}{extension}"
        chemin = self.dossier_local / nom_fichier
        chemin.write_bytes(contenu)
        return f"{self.prefixe_local}{nom_fichier}"

    async def _enregistrer_blob(self, contenu: bytes, extension: str) -> str:
        credentials = _obtenir_credentials_blob()
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="erreur_stockage_blob",
            )

        token, store_id = credentials
        nom_fichier = f"{uuid.uuid4().hex}{extension}"
        pathname = f"{self.sous_dossier}/{nom_fichier}"
        content_type = MIME_PAR_EXTENSION[extension]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{URL_API_BLOB}/?pathname={quote(pathname, safe='')}",
                    content=contenu,
                    headers=_entetes_blob_api(
                        token,
                        store_id,
                        **{
                            "x-vercel-blob-access": "public",
                            "x-add-random-suffix": "0",
                            "x-content-type": content_type,
                        },
                    ),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.exception(
                "Echec upload Vercel Blob (store=%s, path=%s, status=%s)",
                store_id,
                pathname,
                getattr(exc.response, "status_code", None) if isinstance(exc, httpx.HTTPStatusError) else None,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="erreur_stockage_blob",
            ) from exc

        url = data.get("url")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="erreur_stockage_blob",
            )
        return url

    def _supprimer_blob(self, url: str) -> None:
        credentials = _obtenir_credentials_blob()
        if not credentials:
            return

        token, store_id = credentials

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    "DELETE",
                    URL_API_BLOB,
                    json={"url": url},
                    headers=_entetes_blob_api(token, store_id),
                )
                if response.status_code not in (200, 404):
                    response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Echec suppression Vercel Blob (%s)", url)
