"""Service du tableau de bord de la page d'accueil."""

from datetime import date

from sqlalchemy.orm import Session

from backend.app.modules.accueil.schemas import StatsModuleTableauBord, TableauBordAccueil
from backend.app.modules.imprimantes.repository import ImprimanteRepository
from backend.app.modules.imprimantes.schemas import StatutImprimante
from backend.app.modules.imprimantes.statut_imprimante import calculer_statut_depuis_evenements as statut_imprimante
from backend.app.modules.ordinateurs.repository import OrdinateurRepository
from backend.app.modules.ordinateurs.schemas import StatutOrdinateur
from backend.app.modules.ordinateurs.statut_ordinateur import (
    calculer_statut_depuis_evenements as statut_ordinateur,
)
from backend.app.modules.vehicules.repository import VehiculeRepository
from backend.app.modules.vehicules.schemas import StatutItv, StatutVehicule, calculer_statut_itv
from backend.app.modules.vehicules.service import obtenir_journal_actif
from backend.app.modules.vehicules.statut_vehicule import calculer_statut, est_au_garage
from backend.app.modules.vehicules.modeles import Vehicule


def vehicule_disponible_pour_tableau_bord(vehicule: Vehicule, jour: date) -> bool:
    """Disponible sur le panel : libre, pas au garage, ITV non expiree."""
    if est_au_garage(vehicule):
        return False
    if calculer_statut_itv(vehicule.date_expiration_itv, jour) == StatutItv.EXPIREE:
        return False
    journal = obtenir_journal_actif(vehicule, jour)
    utilisateur = journal.utilisateur if journal else None
    return calculer_statut(utilisateur) == StatutVehicule.LIBRE


class AccueilService:
    """Agrege les statistiques des modules actifs pour l'accueil."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir_tableau_bord(self) -> TableauBordAccueil:
        """Calcule les indicateurs affiches sur la page d'accueil."""
        return TableauBordAccueil(
            vehicules=self._stats_vehicules(),
            ordinateurs=self._stats_ordinateurs(),
            imprimantes=self._stats_imprimantes(),
        )

    def _stats_vehicules(self) -> StatsModuleTableauBord:
        vehicules = VehiculeRepository(self.session).obtenir_tous()
        jour = date.today()
        en_service = 0
        indisponible = 0

        for vehicule in vehicules:
            if vehicule_disponible_pour_tableau_bord(vehicule, jour):
                en_service += 1
            else:
                indisponible += 1

        return StatsModuleTableauBord(
            total=len(vehicules),
            en_service=en_service,
            indisponible=indisponible,
        )

    def _stats_ordinateurs(self) -> StatsModuleTableauBord:
        repo = OrdinateurRepository(self.session)
        ordinateurs = repo.obtenir_tous()
        en_service = 0
        indisponible = 0
        modifie = False

        for ordinateur in ordinateurs:
            nouveau = statut_ordinateur(
                ordinateur.evenements,
                ordinateur.utilisateur_assigne,
            ).value
            if ordinateur.statut != nouveau:
                ordinateur.statut = nouveau
                modifie = True
            if nouveau == StatutOrdinateur.OK.value:
                en_service += 1
            else:
                indisponible += 1

        if modifie:
            self.session.commit()

        return StatsModuleTableauBord(
            total=len(ordinateurs),
            en_service=en_service,
            indisponible=indisponible,
        )

    def _stats_imprimantes(self) -> StatsModuleTableauBord:
        repo = ImprimanteRepository(self.session)
        imprimantes = repo.obtenir_tous()
        en_service = 0
        indisponible = 0
        modifie = False

        for imprimante in imprimantes:
            nouveau = statut_imprimante(imprimante.evenements).value
            if imprimante.statut != nouveau:
                imprimante.statut = nouveau
                modifie = True
            if nouveau == StatutImprimante.OK.value:
                en_service += 1
            else:
                indisponible += 1

        if modifie:
            self.session.commit()

        return StatsModuleTableauBord(
            total=len(imprimantes),
            en_service=en_service,
            indisponible=indisponible,
        )
