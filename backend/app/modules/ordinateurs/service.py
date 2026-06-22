"""Logique metier pour le module ordinateurs."""

from datetime import date

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.modules.ordinateurs.modeles import Ordinateur, OrdinateurEvenement
from backend.app.modules.ordinateurs.repository import OrdinateurRepository
from backend.app.modules.ordinateurs.schemas import (
    EvenementCreate,
    EvenementResponse,
    FiltreStatutOrdinateur,
    OrdinateurCreate,
    OrdinateurDetailResponse,
    OrdinateurResponse,
    OrdinateurUpdate,
    ResultatRecherche,
    StatutOrdinateur,
    TypeEvenement,
)
from backend.app.modules.ordinateurs.statut_ordinateur import calculer_statut_depuis_evenements


class OrdinateurService:
    """Service metier pour la gestion des ordinateurs."""

    def __init__(self, session: Session):
        self.repo = OrdinateurRepository(session)

    def _synchroniser_statut(self, ordinateur: Ordinateur) -> bool:
        """Met a jour le statut stocke selon l'historique. Retourne True si modifie."""
        nouveau = calculer_statut_depuis_evenements(
            ordinateur.evenements,
            ordinateur.utilisateur_assigne,
        ).value
        if ordinateur.statut == nouveau:
            return False
        ordinateur.statut = nouveau
        return True

    def _construire_reponse(self, ordinateur: Ordinateur) -> OrdinateurResponse:
        """Construit la reponse (le statut doit etre synchronise avant)."""
        return OrdinateurResponse.model_validate(ordinateur)

    def _appliquer_filtres(
        self,
        ordinateurs: list[Ordinateur],
        statut: FiltreStatutOrdinateur | None = None,
    ) -> list[Ordinateur]:
        """Applique les filtres sur la liste."""
        if statut is None:
            return ordinateurs
        return [
            o
            for o in ordinateurs
            if calculer_statut_depuis_evenements(o.evenements, o.utilisateur_assigne).value
            == statut.value
        ]

    def _verifier_uniques(
        self,
        nom: str,
        numero_serie: str | None,
        ordinateur_id: int | None = None,
    ) -> None:
        """Verifie l'unicite du nom et du numero de serie."""
        autre = self.repo.obtenir_par_nom(nom)
        if autre is not None and autre.id != ordinateur_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nom_existant",
            )
        if numero_serie:
            autre_serie = self.repo.obtenir_par_numero_serie(numero_serie)
            if autre_serie is not None and autre_serie.id != ordinateur_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="numero_serie_existant",
                )

    def _appliquer_donnees_maitres(
        self, ordinateur: Ordinateur, donnees: OrdinateurCreate | OrdinateurUpdate
    ) -> None:
        """Applique les champs modifiables par l'admin."""
        ordinateur.nom = donnees.nom.strip()
        ordinateur.numero_serie = donnees.numero_serie.strip() if donnees.numero_serie else None
        ordinateur.marque = donnees.marque.strip()
        ordinateur.modele = donnees.modele.strip()
        ordinateur.utilisateur_assigne = (
            donnees.utilisateur_assigne.strip() if donnees.utilisateur_assigne else None
        )
        ordinateur.localisation = donnees.localisation.strip()
        ordinateur.systeme_exploitation = (
            donnees.systeme_exploitation.strip() if donnees.systeme_exploitation else None
        )
        ordinateur.processeur = donnees.processeur.strip() if donnees.processeur else None
        ordinateur.memoire_ram = donnees.memoire_ram.strip() if donnees.memoire_ram else None
        ordinateur.capacite_stockage = (
            donnees.capacite_stockage.strip() if donnees.capacite_stockage else None
        )
        ordinateur.date_acquisition = donnees.date_acquisition
        ordinateur.garantie = donnees.garantie.strip() if donnees.garantie else None

    def lister(
        self,
        recherche: str | None = None,
        statut: FiltreStatutOrdinateur | None = None,
    ) -> list[OrdinateurResponse]:
        """Liste les ordinateurs avec filtres."""
        terme = recherche.strip() if recherche else ""
        if terme:
            ordinateurs = self.repo.rechercher(terme)
        else:
            ordinateurs = self.repo.obtenir_tous()

        ordinateurs = self._appliquer_filtres(ordinateurs, statut)
        modifie = False
        reponses = []
        for ordinateur in ordinateurs:
            if self._synchroniser_statut(ordinateur):
                modifie = True
            reponses.append(self._construire_reponse(ordinateur))
        if modifie:
            self.repo.session.commit()
        return reponses

    def obtenir_detail(self, ordinateur_id: int) -> OrdinateurDetailResponse:
        """Retourne le detail avec historique."""
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

        self._synchroniser_statut(ordinateur)
        self.repo.sauvegarder(ordinateur)

        evenements = sorted(
            ordinateur.evenements,
            key=lambda e: (e.date_evenement, e.id),
            reverse=True,
        )
        base = self._construire_reponse(ordinateur)
        return OrdinateurDetailResponse(
            **base.model_dump(),
            evenements=[EvenementResponse.model_validate(e) for e in evenements],
        )

    def creer(self, donnees: OrdinateurCreate) -> OrdinateurResponse:
        """Cree un ordinateur."""
        nom = donnees.nom.strip()
        if not nom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="champs_obligatoires",
            )

        numero_serie = donnees.numero_serie.strip() if donnees.numero_serie else None
        self._verifier_uniques(nom, numero_serie)

        ordinateur = Ordinateur(statut=StatutOrdinateur.OK.value)
        self._appliquer_donnees_maitres(ordinateur, donnees)
        ordinateur = self.repo.creer(ordinateur)
        return self._construire_reponse(ordinateur)

    def creer_admin(self, donnees: OrdinateurCreate) -> OrdinateurResponse:
        """Cree un ordinateur depuis l'admin."""
        return self.creer(donnees)

    def modifier(self, ordinateur_id: int, donnees: OrdinateurUpdate) -> OrdinateurResponse:
        """Modifie les donnees maitres (sans le statut, deduit des evenements)."""
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

        numero_serie = donnees.numero_serie.strip() if donnees.numero_serie else None
        self._verifier_uniques(donnees.nom.strip(), numero_serie, ordinateur_id)
        self._appliquer_donnees_maitres(ordinateur, donnees)
        self._synchroniser_statut(ordinateur)
        ordinateur = self.repo.sauvegarder(ordinateur)
        return self._construire_reponse(ordinateur)

    def modifier_admin(
        self,
        ordinateur_id: int,
        donnees: OrdinateurUpdate,
    ) -> OrdinateurResponse:
        """Met a jour un ordinateur depuis l'admin."""
        return self.modifier(ordinateur_id, donnees)

    def supprimer(self, ordinateur_id: int) -> None:
        """Supprime un ordinateur."""
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )
        self.repo.supprimer(ordinateur)

    def _appliquer_effet_evenement(
        self, ordinateur: Ordinateur, donnees: EvenementCreate
    ) -> None:
        """Met a jour l'ordinateur selon le type d'evenement."""
        type_evt = donnees.type_evenement
        responsable = (
            donnees.utilisateur_responsable.strip()
            if donnees.utilisateur_responsable
            else None
        )

        if type_evt == TypeEvenement.CHANGEMENT_UTILISATEUR:
            ordinateur.utilisateur_assigne = responsable

    def enregistrer_evenement(
        self, ordinateur_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        """Enregistre un evenement et met a jour l'ordinateur."""
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

        evenement = OrdinateurEvenement(
            ordinateur_id=ordinateur_id,
            date_evenement=donnees.date_evenement,
            type_evenement=donnees.type_evenement.value,
            commentaire=donnees.commentaire.strip() if donnees.commentaire else None,
            utilisateur_responsable=(
                donnees.utilisateur_responsable.strip()
                if donnees.utilisateur_responsable
                else None
            ),
        )
        evenement = self.repo.ajouter_evenement(evenement)
        self._appliquer_effet_evenement(ordinateur, donnees)
        self._synchroniser_statut(ordinateur)
        self.repo.sauvegarder(ordinateur)
        self.repo.session.refresh(evenement)

        return EvenementResponse.model_validate(evenement)

    def enregistrer_evenement_depuis_formulaire(
        self, ordinateur_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        """Enregistre un evenement avec gestion des erreurs de validation."""
        try:
            return self.enregistrer_evenement(ordinateur_id, donnees)
        except ValidationError as exc:
            if any(e.get("type") == "value_error" for e in exc.errors()):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="erreur_evenement",
                ) from exc
            raise

    def rechercher_global(self, terme: str) -> list[ResultatRecherche]:
        """Recherche globale pour la page d'accueil."""
        if not terme.strip():
            return []

        ordinateurs = self.repo.rechercher(terme)
        resultats: list[ResultatRecherche] = []
        libelles_statut = {
            StatutOrdinateur.OK: "OK",
            StatutOrdinateur.EN_MAINTENANCE: "Mantenimiento",
            StatutOrdinateur.EN_PANNE: "Averia",
        }

        for ordi in ordinateurs:
            statut = calculer_statut_depuis_evenements(
                ordi.evenements, ordi.utilisateur_assigne
            )
            utilisateur = ordi.utilisateur_assigne or "-"
            resultats.append(
                ResultatRecherche(
                    module_id="ordinateurs",
                    module_libelle="Ordenadores",
                    titre=f"{ordi.nom} ({ordi.marque} {ordi.modele})",
                    sous_titre=f"{ordi.localisation} - {utilisateur} - {libelles_statut[statut]}",
                    route_web="/ordinateurs",
                )
            )

        return resultats
