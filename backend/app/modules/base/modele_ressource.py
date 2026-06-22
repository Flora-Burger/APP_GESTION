"""Contrat de base pour les modules de ressources materielles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleRessource:
    """Description d'un type de materiel gerable dans l'application."""

    id: str
    libelle_es: str
    route_web: str
    route_api: str
    actif: bool
    description_es: str = ""
