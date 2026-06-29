"""Serialisation JSON pour seguro et talleres de referencia."""

import json

from pydantic import BaseModel, Field


class ContactoSeguro(BaseModel):
    """Contacto de seguro avec libelle personnalise."""

    etiqueta: str = Field(default="", max_length=100)
    telefono: str = Field(default="", max_length=30)


class TallerReferencia(BaseModel):
    """Garage de reference."""

    ciudad: str = Field(default="", max_length=100)
    nombre: str = Field(default="", max_length=200)
    telefono: str = Field(default="", max_length=30)
    direccion: str = Field(default="", max_length=300)


def parser_seguro_contactos(valeur: str | None) -> list[ContactoSeguro]:
    if not valeur or not valeur.strip():
        return []
    try:
        donnees = json.loads(valeur)
    except json.JSONDecodeError:
        return []
    if not isinstance(donnees, list):
        return []
    resultat: list[ContactoSeguro] = []
    for entree in donnees:
        if isinstance(entree, dict):
            resultat.append(ContactoSeguro.model_validate(entree))
    return resultat


def serialiser_seguro_contactos(contactos: list[ContactoSeguro]) -> str | None:
    nettoyes = [
        contacto
        for contacto in contactos
        if contacto.etiqueta.strip() or contacto.telefono.strip()
    ]
    if not nettoyes:
        return None
    return json.dumps([c.model_dump() for c in nettoyes], ensure_ascii=False)


def parser_talleres_referencia(valeur: str | None) -> list[TallerReferencia]:
    """Lit la liste des talleres depuis le JSON stocke en base."""
    if not valeur or not valeur.strip():
        return []
    try:
        donnees = json.loads(valeur)
    except json.JSONDecodeError:
        return []
    if not isinstance(donnees, list):
        return []
    resultat: list[TallerReferencia] = []
    for entree in donnees:
        if isinstance(entree, dict):
            resultat.append(TallerReferencia.model_validate(entree))
    return resultat


def serialiser_talleres_referencia(talleres: list[TallerReferencia]) -> str | None:
    """Encode les talleres en JSON pour la base."""
    nettoyees = [
        taller
        for taller in talleres
        if taller.nombre.strip()
        or taller.telefono.strip()
        or taller.direccion.strip()
        or taller.ciudad.strip()
    ]
    if not nettoyees:
        return None
    return json.dumps([taller.model_dump() for taller in nettoyees], ensure_ascii=False)


def talleres_tries_par_ciudad(talleres: list[TallerReferencia]) -> list[TallerReferencia]:
    """Trie les talleres par ville puis par nom."""
    return sorted(
        talleres,
        key=lambda t: (t.ciudad.strip().lower(), t.nombre.strip().lower()),
    )
