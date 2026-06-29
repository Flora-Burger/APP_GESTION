"""Logique metier pour le module imprimantes."""

from datetime import date

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.modules.imprimantes.fichiers_factures import (
    enregistrer_facture_imprimante,
    supprimer_facture_imprimante,
)
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


class ImprimanteService:
    """Service metier pour la gestion des imprimantes."""

    def __init__(self, session: Session):
        self.repo = ImprimanteRepository(session)

    def _construire_reponse(self, imprimante: Imprimante) -> ImprimanteResponse:
        return ImprimanteResponse.model_validate(imprimante)

    def _appliquer_filtres(
        self,
        imprimantes: list[Imprimante],
        statut: FiltreStatutImprimante | None = None,
    ) -> list[Imprimante]:
        if statut is None:
            return imprimantes
        return [i for i in imprimantes if i.statut == statut.value]

    def lister(
        self,
        recherche: str | None = None,
        statut: FiltreStatutImprimante | None = None,
    ) -> list[ImprimanteResponse]:
        terme = recherche.strip() if recherche else ""
        if terme:
            imprimantes = self.repo.rechercher(terme)
        else:
            imprimantes = self.repo.obtenir_tous()
        imprimantes = self._appliquer_filtres(imprimantes, statut)
        return [self._construire_reponse(i) for i in imprimantes]

    def obtenir_detail(self, imprimante_id: int) -> ImprimanteDetailResponse:
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

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
            compteur_pages=0,
        )
        imprimante = self.repo.creer(imprimante)
        return self._construire_reponse(imprimante)

    def modifier(self, imprimante_id: int, donnees: ImprimanteUpdate) -> ImprimanteResponse:
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
        imprimante.fecha_compra = donnees.fecha_compra
        imprimante.tipo_tinta = (donnees.tipo_tinta or "").strip() or None
        imprimante = self.repo.sauvegarder(imprimante)
        return self._construire_reponse(imprimante)

    async def modifier_avec_facture(
        self,
        imprimante_id: int,
        donnees: ImprimanteUpdate,
        facture_fichier: UploadFile | None = None,
    ) -> ImprimanteResponse:
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

        reponse = self.modifier(imprimante_id, donnees)
        if facture_fichier is not None and facture_fichier.filename:
            ancienne = imprimante.facture_url
            nouvelle = await enregistrer_facture_imprimante(facture_fichier)
            imprimante.facture_url = nouvelle
            self.repo.sauvegarder(imprimante)
            if ancienne:
                supprimer_facture_imprimante(ancienne)
            return self._construire_reponse(imprimante)
        return reponse

    def modifier_statut(
        self,
        imprimante_id: int,
        statut: StatutImprimante,
    ) -> ImprimanteResponse:
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )
        imprimante.statut = statut.value
        imprimante = self.repo.sauvegarder(imprimante)
        return self._construire_reponse(imprimante)

    def supprimer(self, imprimante_id: int) -> None:
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )
        facture = imprimante.facture_url
        self.repo.supprimer(imprimante)
        if facture:
            supprimer_facture_imprimante(facture)

    def enregistrer_evenement(
        self, imprimante_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        imprimante = self.repo.obtenir_par_id(imprimante_id)
        if imprimante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="imprimante_introuvable",
            )

        if donnees.type_evenement == TypeEvenement.TONER:
            imprimante.date_dernier_toner = donnees.date_evenement

        evenement = ImprimanteEvenement(
            imprimante_id=imprimante_id,
            date_evenement=donnees.date_evenement,
            type_evenement=donnees.type_evenement.value,
            compteur_pages=None,
            commentaire=donnees.commentaire.strip() if donnees.commentaire else None,
        )
        evenement = self.repo.ajouter_evenement(evenement)
        self.repo.sauvegarder(imprimante)
        self.repo.session.refresh(evenement)
        return EvenementResponse.model_validate(evenement)

    def enregistrer_evenement_depuis_formulaire(
        self, imprimante_id: int, donnees: EvenementCreate
    ) -> EvenementResponse:
        return self.enregistrer_evenement(imprimante_id, donnees)

    def rechercher_global(self, terme: str) -> list[ResultatRecherche]:
        if not terme.strip():
            return []

        imprimantes = self.repo.rechercher(terme)
        resultats: list[ResultatRecherche] = []

        for imp in imprimantes:
            resultats.append(
                ResultatRecherche(
                    module_id="imprimantes",
                    module_libelle="Impresoras",
                    titre=f"{imp.nom} ({imp.modele})",
                    sous_titre=f"{imp.localisation} - {imp.statut.upper()}",
                    route_web="/imprimantes",
                )
            )

        return resultats
