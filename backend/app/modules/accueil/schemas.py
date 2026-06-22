"""Schemas pour le tableau de bord de la page d'accueil."""

from pydantic import BaseModel, computed_field


class StatsModuleTableauBord(BaseModel):
    """Indicateurs communs par module pour l'accueil."""

    total: int
    en_service: int
    indisponible: int


class TableauBordAccueil(BaseModel):
    """Resume global du parc materiel."""

    vehicules: StatsModuleTableauBord
    ordinateurs: StatsModuleTableauBord
    imprimantes: StatsModuleTableauBord

    @computed_field
    @property
    def alertes_total(self) -> int:
        """Nombre d'elements indisponibles sur l'ensemble du parc."""
        return (
            self.vehicules.indisponible
            + self.ordinateurs.indisponible
            + self.imprimantes.indisponible
        )
