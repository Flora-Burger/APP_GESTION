"""Registre central des modules de ressources materielles."""

from backend.app.modules.base.modele_ressource import ModuleRessource

MODULES_RESSOURCES: list[ModuleRessource] = [
    ModuleRessource(
        id="vehicules",
        libelle_es="Vehiculos",
        route_web="/vehicules",
        route_api="/api/v1/vehicules",
        actif=True,
        description_es="Gestion y consulta de vehiculos de empresa",
    ),
    ModuleRessource(
        id="ordinateurs",
        libelle_es="Ordenadores",
        route_web="/ordinateurs",
        route_api="/api/v1/ordinateurs",
        actif=True,
        description_es="Gestion del parque informatico de empresa",
    ),
    ModuleRessource(
        id="imprimantes",
        libelle_es="Impresoras",
        route_web="/imprimantes",
        route_api="/api/v1/imprimantes",
        actif=True,
        description_es="Gestion de impresoras y seguimiento de contador",
    ),
]


def obtenir_modules_actifs() -> list[ModuleRessource]:
    """Retourne uniquement les modules actifs."""
    return [m for m in MODULES_RESSOURCES if m.actif]


def obtenir_tous_modules() -> list[ModuleRessource]:
    """Retourne tous les modules enregistres."""
    return list(MODULES_RESSOURCES)
