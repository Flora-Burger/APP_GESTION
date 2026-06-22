"""Logique metier pour le module imprimantes."""

from datetime import date

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.modules.imprimantes.modeles import Imprimante, ImprimanteEvenement
from backend.app.modules.imprimantes.repository import ImprimanteRepository
from backend.app.modules.imprimantes.schemas import (
    EvenementCreate,
    EvenementResponse,
    FiltreStatutImprimante,
    ImprimanteCreate,
    ImprimanteDetailResponse,
    ImprimanteResponse,
    ImprimanteUpdate,
    ResultatRecherche,
    StatutImprimante,
    TypeEvenement,
)
from backend.app.modules.imprimantes.statut_imprimante import calculer_statut_depuis_evenements


class ImprimanteService:
    """Service metier pour la gestion des imprimantes."""

    def __init__(self, session: Session):
        self.repo = ImprimanteRepository(session)

    def _synchroniser_statut(self, imprimante: Imprimante) -> bool:
        """Met a jour le statut stocke selon l'historique. Retourne True si modifie."""
        nouveau = calculer_statut_depuis_evenements(imprimante.evenements).value
        if imprimante.statut == nouveau:
            return False
        imprimante.statut = nouveau
        return True

    def _construire_reponse(self, imprimante: Imprimante) -> ImprimanteResponse:
        """Construit la reponse (le statut doit etre synchronise avant)."""
        return ImprimanteResponse.model_validate(imprimante)

    def _appliquer_filtres(
        self,
        imprimantes: list[Imprimante],
        statut: FiltreStatutImprimante | None = None,
    ) -> list[Imprimante]:
        """Applique les filtres sur la liste."""
        if statut is None:
            return imprimantes
        return [
            i
            for i in imprimantes
            if calculer_statut_depuis_evenements(i.evenements).value == statut.value
        ]

    def lister(
        self,
        recherche: str | None = None,
        statut: FiltreStatutImprimante | None = None,
    ) -> list[ImprimanteResponse]:
        """Liste les imprimantes avec filtres."""
        terme = recherche.strip() if recherche else ""
        if terme:
            imprimantes = self.repo.rechercher(terme)
        else:
            imprimantes = self.repo.obtenir_tous()

        imprimantes = self._appliquer_filtres(imprimantes, statut)
        modifie = False
        reponses = []
        for imprimante in imprimantes:
            if self._synchroniser_statut(imprimante):
                modifie = True
            reponses.append(self._construire_reponse(imprimante))
        if modifie:
            self.repo.session.commit()
        return reponses

    def obtenir_detail(self, imprimante_id: int) -> ImprimanteDetailResponse:
        """Retourne le detail avec historique."""
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

        self._synchroniser_statut(imprimante)
        self.repo.sauvegarder(imprimante)

        evenements = sorted(
            imprimante.evenements,
            key=lambda e: (e.date_evenement, e.id),
            reverse=True,
        )
        base = ImprimanteResponse.model_validate(imprimante)
        return ImprimanteDetailResponse(
            **base.model_dump(),
            evenements=[EvenementResponse.model_validate(e) for e in evenements],
        )

    def creer(self, donnees: ImprimanteCreate) -> ImprimanteResponse:
        """Cree une imprimante et un evenement d'installation."""
        nom = donnees.nom.strip()
        if not nom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="champs_obligatoires",
            )

        if self.repo.obtenir_par_nom(nom):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nom_existant",
            )

        imprimante = Imprimante(
            nom=nom,
            modele=donnees.modele.strip(),
            localisation=donnees.localisation.strip(),
            statut=StatutImprimante.OK.value,
            compteur_pages=donnees.compteur_initial,
        )
        imprimante = self.repo.creer(imprimante)

        if donnees.compteur_initial > 0:
            evenement = ImprimanteEvenement(
                imprimante_id=imprimante.id,
                date_evenement=date.today(),
                type_evenement=TypeEvenement.COMPTEUR.value,
                compteur_pages=donnees.compteur_initial,
                commentaire="Instalacion",
            )
            self.repo.ajouter_evenement(evenement)
            self.repo.sauvegarder(imprimante)

        return self._construire_reponse(imprimante)

    def modifier(self, imprimante_id: int, donnees: ImprimanteUpdate) -> ImprimanteResponse:
        """Modifie les donnees maitres (sans le statut, deduit des evenements)."""
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

        nom = donnees.nom.strip()
        autre = self.repo.obtenir_par_nom(nom)
        if autre is not None and autre.id != imprimante_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nom_existant",
            )

        imprimante.nom = nom
        imprimante.modele = donnees.modele.strip()
        imprimante.localisation = donnees.localisation.strip()
        self._synchroniser_statut(imprimante)
        imprimante = self.repo.sauvegarder(imprimante)
        return self._construire_reponse(imprimante)

    def supprimer(self, imprimante_id: int) -> None:
        """Supprime une imprimante."""
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )
        self.repo.supprimer(imprimante)

    def _mettre_a_jour_compteur(self, imprimante: Imprimante, compteur: int | None) -> None:
        """Met a jour le compteur si une valeur est fournie."""
        if compteur is None:
            return
        if compteur < imprimante.compteur_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="compteur_regressif",
            )
        imprimante.compteur_pages = compteur

    def enregistrer_evenement(
        self, imprimante_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        """Enregistre un evenement et met a jour l'imprimante."""
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

        type_evt = donnees.type_evenement

        if type_evt == TypeEvenement.COMPTEUR:
            self._mettre_a_jour_compteur(imprimante, donnees.compteur_pages)
        elif type_evt == TypeEvenement.TONER:
            imprimante.date_dernier_toner = donnees.date_evenement
            self._mettre_a_jour_compteur(imprimante, donnees.compteur_pages)
        elif type_evt == TypeEvenement.MAINTENANCE_TERMINEE:
            imprimante.date_derniere_maintenance = donnees.date_evenement
            self._mettre_a_jour_compteur(imprimante, donnees.compteur_pages)
        elif type_evt in (
            TypeEvenement.MAINTENANCE,
            TypeEvenement.PANNE,
            TypeEvenement.REPARATION,
        ):
            self._mettre_a_jour_compteur(imprimante, donnees.compteur_pages)

        evenement = ImprimanteEvenement(
            imprimante_id=imprimante_id,
            date_evenement=donnees.date_evenement,
            type_evenement=type_evt.value,
            compteur_pages=donnees.compteur_pages,
            commentaire=donnees.commentaire.strip() if donnees.commentaire else None,
        )
        evenement = self.repo.ajouter_evenement(evenement)
        self._synchroniser_statut(imprimante)
        self.repo.sauvegarder(imprimante)
        self.repo.session.refresh(evenement)

        return EvenementResponse.model_validate(evenement)

    def enregistrer_evenement_depuis_formulaire(
        self, imprimante_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        """Enregistre un evenement avec gestion des erreurs de validation."""
        try:
            return self.enregistrer_evenement(imprimante_id, donnees)
        except ValidationError as exc:
            if any(e.get("type") == "value_error" for e in exc.errors()):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="compteur_obligatoire",
                ) from exc
            raise

    def rechercher_global(self, terme: str) -> list[ResultatRecherche]:
        """Recherche globale pour la page d'accueil."""
        if not terme.strip():
            return []

        imprimantes = self.repo.rechercher(terme)
        resultats: list[ResultatRecherche] = []

        for imp in imprimantes:
            statut = calculer_statut_depuis_evenements(imp.evenements)
            resultats.append(
                ResultatRecherche(
                    module_id="imprimantes",
                    module_libelle="Impresoras",
                    titre=f"{imp.nom} ({imp.modele})",
                    sous_titre=f"{imp.localisation} - {statut.value.upper()}",
                    route_web="/imprimantes",
                )
            )

        return resultats
