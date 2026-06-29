"""Gestion des factures uploadées pour les imprimantes."""

from fastapi import UploadFile

from backend.app.core.stockage_fichiers import StockageFichiers

_stockage = StockageFichiers("imprimantes/factures")


async def enregistrer_facture_imprimante(fichier: UploadFile) -> str:
    """Enregistre une facture et retourne son URL publique."""
    return await _stockage.enregistrer_document(fichier)


def supprimer_facture_imprimante(url: str) -> None:
    """Supprime une facture gérée (locale ou Vercel Blob)."""
    _stockage.supprimer(url)
