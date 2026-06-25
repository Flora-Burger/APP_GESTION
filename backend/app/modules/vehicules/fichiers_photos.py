"""Gestion des fichiers photo uploades pour les vehicules."""

from pathlib import Path

from fastapi import UploadFile

from backend.app.core.stockage_fichiers import StockageFichiers

_stockage = StockageFichiers("vehicules")

DOSSIER_UPLOADS = _stockage.dossier_local
PREFIXE_URL_LOCALE = _stockage.prefixe_local


def est_photo_locale(url: str) -> bool:
    """Indique si l'URL pointe vers un fichier gere par l'application."""
    return _stockage.est_photo_geree(url)


def chemin_fichier_depuis_url(url: str) -> Path | None:
    """Retourne le chemin disque d'une photo locale."""
    return _stockage.chemin_fichier_local_depuis_url(url)


async def enregistrer_photo_vehicule(fichier: UploadFile) -> str:
    """Enregistre une photo uploadée et retourne son URL publique."""
    return await _stockage.enregistrer(fichier)


def supprimer_photo_locale(url: str) -> None:
    """Supprime une photo geree (locale ou Vercel Blob)."""
    _stockage.supprimer(url)
