"""Calcul du statut affiche d'un vehicule."""

from datetime import date

from backend.app.modules.vehicules.modeles import Vehicule, VehiculeImmobilisation
from backend.app.modules.vehicules.schemas import (
    StatutAffichageVehicule,
    StatutItv,
    StatutVehicule,
    calculer_statut_itv,
)


def calculer_statut(utilisateur: str | None) -> StatutVehicule:
    """Calcule le statut libre/occupe a partir de l'utilisateur."""
    if utilisateur is None or utilisateur.strip() == "":
        return StatutVehicule.LIBRE
    return StatutVehicule.OCCUPE


def obtenir_immobilisation_active(
    vehicule: Vehicule,
) -> VehiculeImmobilisation | None:
    """Retourne l'immobilisation en cours, s'il y en a une."""
    for immobilisation in vehicule.immobilisations:
        if immobilisation.date_fin is None:
            return immobilisation
    return None


def calculer_statut_affichage(
    vehicule: Vehicule,
    utilisateur: str | None,
    jour: date | None = None,
) -> StatutAffichageVehicule:
    """Statut visible sur la fiche (priorite au garage, puis ITV vencida)."""
    if obtenir_immobilisation_active(vehicule) is not None:
        return StatutAffichageVehicule.AU_GARAGE
    reference = jour or date.today()
    if calculer_statut_itv(vehicule.date_expiration_itv, reference) == StatutItv.EXPIREE:
        return StatutAffichageVehicule.NO_DISPONIBLE
    statut = calculer_statut(utilisateur)
    if statut == StatutVehicule.LIBRE:
        return StatutAffichageVehicule.DISPONIBLE
    return StatutAffichageVehicule.OCCUPE


def est_au_garage(vehicule: Vehicule) -> bool:
    """Indique si le vehicule est actuellement immobilise."""
    return obtenir_immobilisation_active(vehicule) is not None
