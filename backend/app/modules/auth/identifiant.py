"""Validation et normalisation de l'identifiant utilisateur (3 chiffres)."""

import re

_IDENTIFIANT_VALIDE = re.compile(r"^\d{3}$")
ID_UTILISATEUR_LIBRE = "000"


def normaliser_identifiant(valeur: str) -> str:
    """Verifie et retourne un identifiant sur exactement 3 chiffres (000-999)."""
    brut = valeur.strip()
    if not _IDENTIFIANT_VALIDE.fullmatch(brut):
        raise ValueError("identifiant_invalide")
    return brut
