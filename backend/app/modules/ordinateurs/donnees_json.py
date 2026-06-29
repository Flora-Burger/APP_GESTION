"""Serialisation JSON pour les licences ordinateur."""

import json

from pydantic import BaseModel, Field


class LicenceLogiciel(BaseModel):
    """Licence installee sur un ordinateur."""

    nom: str = Field(default="", max_length=150)
    expiration: str | None = Field(default=None, max_length=20)


def parser_licences(valeur: str | None) -> list[LicenceLogiciel]:
    """Lit les licences depuis le JSON stocke en base."""
    if not valeur or not valeur.strip():
        return []
    try:
        donnees = json.loads(valeur)
    except json.JSONDecodeError:
        return []
    if not isinstance(donnees, list):
        return []
    resultat: list[LicenceLogiciel] = []
    for entree in donnees:
        if isinstance(entree, dict):
            resultat.append(LicenceLogiciel.model_validate(entree))
    return resultat


def serialiser_licences(licences: list[LicenceLogiciel]) -> str | None:
    """Encode les licences en JSON pour la base."""
    nettoyees = [licence for licence in licences if licence.nom.strip()]
    if not nettoyees:
        return None
    return json.dumps([licence.model_dump() for licence in nettoyees], ensure_ascii=False)
