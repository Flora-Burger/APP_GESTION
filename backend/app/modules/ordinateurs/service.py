"""Logique metier pour le module ordinateurs."""

from datetime import date

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.modules.ordinateurs.donnees_json import (
    LicenceLogiciel,
    parser_licences,
    serialiser_licences,
)
from backend.app.modules.ordinateurs.fichiers_factures import (
    enregistrer_facture_ordinateur,
    supprimer_facture_ordinateur,
)
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
)


class OrdinateurService:
    """Service metier pour la gestion des ordinateurs."""

    def __init__(self, session: Session):
        self.repo = OrdinateurRepository(session)

    def _construire_reponse(self, ordinateur: Ordinateur) -> OrdinateurResponse:
        return OrdinateurResponse(
            id=ordinateur.id,
            nom=ordinateur.nom,
            numero_serie=ordinateur.numero_serie,
            marque=ordinateur.marque,
            modele=ordinateur.modele,
            utilisateur_assigne=ordinateur.utilisateur_assigne,
            localisation=ordinateur.localisation,
            statut=ordinateur.statut,
            systeme_exploitation=ordinateur.systeme_exploitation,
            processeur=ordinateur.processeur,
            memoire_ram=ordinateur.memoire_ram,
            capacite_stockage=ordinateur.capacite_stockage,
            date_acquisition=ordinateur.date_acquisition,
            garantie=ordinateur.garantie,
            facture_url=ordinateur.facture_url,
            licences=parser_licences(ordinateur.licences),
            cree_le=ordinateur.cree_le,
        )

    def _appliquer_filtres(
        self,
        ordinateurs: list[Ordinateur],
        statut: FiltreStatutOrdinateur | None = None,
    ) -> list[Ordinateur]:
        if statut is None:
            return ordinateurs
        return [o for o in ordinateurs if o.statut == statut.value]

    def _verifier_uniques(
        self,
        nom: str,
        numero_serie: str | None,
        ordinateur_id: int | None = None,
    ) -> None:
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
        self,
        ordinateur: Ordinateur,
        donnees: OrdinateurCreate | OrdinateurUpdate,
        licences: list[LicenceLogiciel] | None = None,
    ) -> None:
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
        if licences is not None:
            ordinateur.licences = serialiser_licences(licences)

    def lister(
        self,
        recherche: str | None = None,
        statut: FiltreStatutOrdinateur | None = None,
    ) -> list[OrdinateurResponse]:
        terme = recherche.strip() if recherche else ""
        if terme:
            ordinateurs = self.repo.rechercher(terme)
        else:
            ordinateurs = self.repo.obtenir_tous()
        ordinateurs = self._appliquer_filtres(ordinateurs, statut)
        return [self._construire_reponse(o) for o in ordinateurs]

    def obtenir_detail(self, ordinateur_id: int) -> OrdinateurDetailResponse:
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

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
        return self.creer(donnees)

    def modifier(
        self,
        ordinateur_id: int,
        donnees: OrdinateurUpdate,
        licences: list[LicenceLogiciel] | None = None,
    ) -> OrdinateurResponse:
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

        numero_serie = donnees.numero_serie.strip() if donnees.numero_serie else None
        self._verifier_uniques(donnees.nom.strip(), numero_serie, ordinateur_id)
        self._appliquer_donnees_maitres(ordinateur, donnees, licences=licences)
        ordinateur = self.repo.sauvegarder(ordinateur)
        return self._construire_reponse(ordinateur)

    async def modifier_avec_facture(
        self,
        ordinateur_id: int,
        donnees: OrdinateurUpdate,
        facture_fichier: UploadFile | None = None,
        licences: list[LicenceLogiciel] | None = None,
    ) -> OrdinateurResponse:
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )

        reponse = self.modifier(ordinateur_id, donnees, licences=licences)
        if facture_fichier is not None and facture_fichier.filename:
            ancienne = ordinateur.facture_url
            nouvelle = await enregistrer_facture_ordinateur(facture_fichier)
            ordinateur.facture_url = nouvelle
            self.repo.sauvegarder(ordinateur)
            if ancienne:
                supprimer_facture_ordinateur(ancienne)
            return self._construire_reponse(ordinateur)
        return reponse

    def modifier_admin(
        self,
        ordinateur_id: int,
        donnees: OrdinateurUpdate,
        licences: list[LicenceLogiciel] | None = None,
    ) -> OrdinateurResponse:
        return self.modifier(ordinateur_id, donnees, licences=licences)

    def modifier_statut(
        self,
        ordinateur_id: int,
        statut: StatutOrdinateur,
    ) -> OrdinateurResponse:
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )
        ordinateur.statut = statut.value
        ordinateur = self.repo.sauvegarder(ordinateur)
        return self._construire_reponse(ordinateur)

    def supprimer(self, ordinateur_id: int) -> None:
        ordinateur = self.repo.obtenir_par_id(ordinateur_id)
        if ordinateur is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ordinateur_introuvable",
            )
        facture = ordinateur.facture_url
        self.repo.supprimer(ordinateur)
        if facture:
            supprimer_facture_ordinateur(facture)

    def enregistrer_evenement(
        self, ordinateur_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
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
            utilisateur_responsable=None,
        )
        evenement = self.repo.ajouter_evenement(evenement)
        self.repo.sauvegarder(ordinateur)
        self.repo.session.refresh(evenement)
        return EvenementResponse.model_validate(evenement)

    def enregistrer_evenement_depuis_formulaire(
        self, ordinateur_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        return self.enregistrer_evenement(ordinateur_id, donnees)

    def rechercher_global(self, terme: str) -> list[ResultatRecherche]:
        if not terme.strip():
            return []

        ordinateurs = self.repo.rechercher(terme)
        resultats: list[ResultatRecherche] = []
        libelles_statut = {
            StatutOrdinateur.OK.value: "OK",
            StatutOrdinateur.EN_MAINTENANCE.value: "Mantenimiento",
            StatutOrdinateur.EN_PANNE.value: "Averia",
        }

        for ordi in ordinateurs:
            utilisateur = ordi.utilisateur_assigne or "-"
            resultats.append(
                ResultatRecherche(
                    module_id="ordinateurs",
                    module_libelle="Ordenadores",
                    titre=f"{ordi.nom} ({ordi.marque} {ordi.modele})",
                    sous_titre=f"{ordi.localisation} - {utilisateur} - {libelles_statut.get(ordi.statut, ordi.statut)}",
                    route_web="/ordinateurs",
                )
            )

        return resultats
