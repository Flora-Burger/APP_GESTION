"""Logique metier pour le module vehicules."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.modules.auth.affichage import obtenir_nom_affichage, peut_actualizar_donnees_vehicule
from backend.app.modules.auth.modeles import Utilisateur
from backend.app.modules.vehicules.configuration_service import ConfigurationVehiculesService
from backend.app.modules.vehicules.fichiers_photos import (
    enregistrer_photo_vehicule,
    supprimer_photo_locale,
)
from backend.app.modules.vehicules.images_vehicules import obtenir_url_photo
from backend.app.modules.vehicules.modeles import Vehicule, VehiculeImmobilisation, VehiculeJournal
from backend.app.modules.vehicules.repository import VehiculeRepository
from backend.app.modules.vehicules.schemas import (
    DonneesJourVehicule,
    FiltreItv,
    FiltreKmJour,
    FiltreStatut,
    ImmobilisationCreate,
    ImmobilisationResponse,
    ItvUpdate,
    RemiseEnServiceCreate,
    ResultatRecherche,
    StatutItv,
    StatutVehicule,
    VehiculeCreate,
    VehiculeCreateAdmin,
    VehiculeDetailResponse,
    VehiculeJournalCreate,
    VehiculeJournalResponse,
    VehiculeResponse,
    VehiculeUpdateAdmin,
    calculer_statut_itv,
    kilometrage_jour_correspond_au_filtre,
)
from backend.app.modules.vehicules.statut_vehicule import (
    calculer_statut,
    calculer_statut_affichage,
    est_au_garage,
    obtenir_immobilisation_active,
)


def obtenir_journal_actif(
    vehicule: Vehicule, date_reference: date | None = None
) -> VehiculeJournal | None:
    """Retourne l'utilisation active pour la date de reference."""
    jour = date_reference or date.today()
    actifs = [
        journal
        for journal in vehicule.journaux
        if journal.date_jour == jour
        and journal.actif
        and journal.utilisateur
        and journal.utilisateur.strip()
    ]
    if not actifs:
        return None
    return max(actifs, key=lambda journal: journal.id)


def obtenir_journaux_du_jour(
    vehicule: Vehicule, date_reference: date | None = None
) -> list[VehiculeJournal]:
    """Retourne toutes les entrees journalieres d'une date (actives ou non)."""
    jour = date_reference or date.today()
    return [journal for journal in vehicule.journaux if journal.date_jour == jour]


def obtenir_totaux_jour(
    vehicule: Vehicule, date_reference: date | None = None
) -> tuple[int, Decimal, Decimal]:
    """Cumule km, litres et cout de tous les utilisateurs du jour."""
    km_total = 0
    consommation_totale = Decimal("0.00")
    cout_total = Decimal("0.00")
    for journal in obtenir_journaux_du_jour(vehicule, date_reference):
        km_total += journal.kilometrage_jour
        consommation_totale += journal.consommation_jour
        cout_total += journal.cout_carburant_jour
    return km_total, consommation_totale, cout_total


def obtenir_journal_du_jour(
    vehicule: Vehicule, date_reference: date | None = None
) -> VehiculeJournal | None:
    """Alias : entree active du jour (compatibilite)."""
    return obtenir_journal_actif(vehicule, date_reference)


def obtenir_utilisateur_effectif(
    vehicule: Vehicule, date_reference: date | None = None
) -> str | None:
    """Retourne l'utilisateur assigne au vehicule (champ permanent, journal en secours)."""
    assigne = (vehicule.utilisateur_assigne or "").strip()
    if assigne:
        return assigne
    journal = obtenir_journal_actif(vehicule, date_reference)
    if journal and journal.utilisateur and journal.utilisateur.strip():
        return journal.utilisateur.strip()
    return None


def formater_modele_affiche(vehicule: Vehicule) -> str:
    """Formate le modele affiche (marque + modele si distinct)."""
    if vehicule.marque and vehicule.marque.lower() not in vehicule.modele.lower():
        return f"{vehicule.marque} {vehicule.modele}".strip()
    return vehicule.modele.strip()


def appliquer_mise_a_jour_kilometrage(
    vehicule: Vehicule,
    journal: VehiculeJournal,
    nouveau_kilometrage: int,
) -> int:
    """Met a jour le kilometrage vehicule et journal. Retourne le delta du jour."""
    ancien = vehicule.kilometrage_actuel
    if nouveau_kilometrage < ancien:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="kilometrage_invalide",
        )
    delta = nouveau_kilometrage - ancien
    journal.kilometrage_jour += delta
    journal.kilometrage_actuel = nouveau_kilometrage
    vehicule.kilometrage_actuel = nouveau_kilometrage
    return delta


def journal_a_donnees_historique(journal: VehiculeJournalResponse) -> bool:
    """True si l'entree contient au moins une donnee km, carburant ou cout."""
    return (
        journal.kilometrage_jour > 0
        or journal.consommation_jour > 0
        or journal.cout_carburant_jour > 0
    )


def filtrer_journaux_historique(
    journaux: list[VehiculeJournalResponse],
    recherche_utilisateur: str | None = None,
    recherche_date: date | None = None,
) -> list[VehiculeJournalResponse]:
    """Filtre les entrees journalieres de l'historique."""
    resultat = [journal for journal in journaux if journal_a_donnees_historique(journal)]
    terme = recherche_utilisateur.strip() if recherche_utilisateur else ""
    if terme:
        terme_min = terme.lower()
        resultat = [
            journal
            for journal in resultat
            if journal.utilisateur and terme_min in journal.utilisateur.lower()
        ]
    if recherche_date is not None:
        resultat = [
            journal for journal in resultat if journal.date_jour == recherche_date
        ]
    return resultat


def filtrer_immobilisations_historique(
    immobilisations: list[ImmobilisationResponse],
    recherche_utilisateur: str | None = None,
    recherche_date: date | None = None,
) -> list[ImmobilisationResponse]:
    """Filtre les immobilisations de l'historique."""
    if recherche_utilisateur and recherche_utilisateur.strip():
        return []

    if recherche_date is None:
        return immobilisations

    resultat: list[ImmobilisationResponse] = []
    for immobilisation in immobilisations:
        fin = immobilisation.date_fin or date.today()
        if immobilisation.date_debut <= recherche_date <= fin:
            resultat.append(immobilisation)
    return resultat


class VehiculeService:
    """Service metier pour la gestion des vehicules."""

    def __init__(self, session: Session):
        self.repo = VehiculeRepository(session)
        self.config_service = ConfigurationVehiculesService(session)

    def _assurer_photo(self, vehicule: Vehicule) -> str:
        """Resout et persiste l'image si absente."""
        url = obtenir_url_photo(vehicule)
        if not vehicule.photo_url or not vehicule.photo_url.strip():
            vehicule.photo_url = url
            self.repo.session.commit()
        return url

    def _construire_reponse(
        self, vehicule: Vehicule, date_reference: date | None = None
    ) -> VehiculeResponse:
        """Construit la reponse avec les donnees du jour."""
        jour = date_reference or date.today()
        self._assurer_journal_assignation_jour(vehicule, jour)
        journal_jour = self.repo.obtenir_journal_actif(vehicule.id, jour)
        if journal_jour is None:
            journal_jour = obtenir_journal_actif(vehicule, jour)
        if not (vehicule.utilisateur_assigne or "").strip() and journal_jour and journal_jour.utilisateur:
            vehicule.utilisateur_assigne = journal_jour.utilisateur.strip()
            vehicule = self.repo.sauvegarder(vehicule)
        utilisateur = obtenir_utilisateur_effectif(vehicule, jour)
        km_jour, conso_jour, cout_jour = obtenir_totaux_jour(vehicule, jour)
        photo = self._assurer_photo(vehicule)
        immobilisation = obtenir_immobilisation_active(vehicule)
        config = self.config_service.obtenir()

        return VehiculeResponse(
            id=vehicule.id,
            matricule=vehicule.matricule,
            marque=vehicule.marque,
            modele=vehicule.modele,
            modele_affiche=formater_modele_affiche(vehicule),
            photo_url=vehicule.photo_url,
            photo_url_affiche=photo,
            date_expiration_itv=vehicule.date_expiration_itv,
            consommation_moyenne=vehicule.consommation_moyenne,
            statut=calculer_statut(utilisateur),
            statut_affichage=calculer_statut_affichage(vehicule, utilisateur, jour),
            statut_itv=calculer_statut_itv(vehicule.date_expiration_itv, jour),
            immobilisation_active=(
                ImmobilisationResponse.model_validate(immobilisation)
                if immobilisation is not None
                else None
            ),
            utilisateur_jour=utilisateur,
            kilometrage_actuel=vehicule.kilometrage_actuel,
            kilometrage_jour_aujourdhui=km_jour,
            consommation_jour_aujourdhui=conso_jour,
            cout_carburant_jour_aujourdhui=cout_jour,
            consommation_session_aujourdhui=(
                journal_jour.consommation_jour if journal_jour else Decimal("0.00")
            ),
            cout_session_aujourdhui=(
                journal_jour.cout_carburant_jour if journal_jour else Decimal("0.00")
            ),
            utilisateur_assigne=vehicule.utilisateur_assigne,
            seguro_compania=config.seguro_compania,
            seguro_poliza=config.seguro_poliza,
            seguro_contactos=config.seguro_contactos,
            talleres_referencia=config.talleres_referencia,
        )

    def _appliquer_filtres(
        self,
        vehicules: list[Vehicule],
        statut: FiltreStatut | None = None,
        itv: FiltreItv | None = None,
        km_jour: FiltreKmJour | None = None,
    ) -> list[Vehicule]:
        """Applique les filtres sur la liste de vehicules."""
        resultat = vehicules
        jour = date.today()

        if statut is not None:
            if statut == FiltreStatut.AU_GARAGE:
                resultat = [v for v in resultat if est_au_garage(v)]
            else:
                resultat = [
                    v
                    for v in resultat
                    if not est_au_garage(v)
                    and calculer_statut(obtenir_utilisateur_effectif(v, jour)).value
                    == statut.value
                ]

        if itv is not None:
            resultat = [
                v
                for v in resultat
                if calculer_statut_itv(v.date_expiration_itv, jour).value == itv.value
            ]

        if km_jour is not None:
            resultat = [
                v
                for v in resultat
                if kilometrage_jour_correspond_au_filtre(
                    obtenir_totaux_jour(v, jour)[0],
                    km_jour,
                )
            ]

        return resultat

    def lister(
        self,
        recherche: str | None = None,
        statut: FiltreStatut | None = None,
        itv: FiltreItv | None = None,
        km_jour: FiltreKmJour | None = None,
        utilisateur_assigne: str | None = None,
    ) -> list[VehiculeResponse]:
        """Liste les vehicules avec filtres et recherche."""
        terme = recherche.strip() if recherche else ""
        if terme:
            vehicules = self.repo.rechercher(terme)
        else:
            vehicules = self.repo.obtenir_tous()

        if utilisateur_assigne:
            filtre = utilisateur_assigne.strip().lower()
            vehicules = [
                v
                for v in vehicules
                if v.utilisateur_assigne
                and v.utilisateur_assigne.strip().lower() == filtre
            ]

        vehicules = self._appliquer_filtres(vehicules, statut, itv, km_jour)
        return [self._construire_reponse(v) for v in vehicules]

    def obtenir_detail(self, vehicule_id: int) -> VehiculeDetailResponse:
        """Retourne le detail d'un vehicule avec historique."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicule non trouve",
            )

        base = self._construire_reponse(vehicule)
        journaux = sorted(
            vehicule.journaux,
            key=lambda journal: (journal.date_jour, journal.id),
            reverse=True,
        )
        immobilisations = sorted(
            vehicule.immobilisations,
            key=lambda immobilisation: (immobilisation.date_debut, immobilisation.id),
            reverse=True,
        )

        return VehiculeDetailResponse(
            **base.model_dump(),
            journaux=[
                self._journal_en_reponse(vehicule, journal) for journal in journaux
            ],
            immobilisations=[
                ImmobilisationResponse.model_validate(i) for i in immobilisations
            ],
        )

    def _journal_en_reponse(
        self, vehicule: Vehicule, journal: VehiculeJournal
    ) -> VehiculeJournalResponse:
        """Construit une entree journaliere pour l'historique."""
        return VehiculeJournalResponse.model_validate(journal)

    def obtenir_historique(
        self,
        vehicule_id: int,
        recherche_utilisateur: str | None = None,
        recherche_date: date | None = None,
    ) -> VehiculeDetailResponse:
        """Retourne l'historique d'un vehicule, avec filtres optionnels."""
        detail = self.obtenir_detail(vehicule_id)
        journaux = filtrer_journaux_historique(
            detail.journaux, recherche_utilisateur, recherche_date
        )
        if recherche_utilisateur or recherche_date is not None:
            immobilisations = filtrer_immobilisations_historique(
                detail.immobilisations, recherche_utilisateur, recherche_date
            )
        else:
            immobilisations = detail.immobilisations

        return detail.model_copy(
            update={
                "journaux": journaux,
                "immobilisations": immobilisations,
            }
        )

    def creer(self, donnees: VehiculeCreate) -> VehiculeResponse:
        """Cree un nouveau vehicule."""
        if self.repo.obtenir_par_matricule(donnees.matricule):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Matricule deja existant",
            )

        vehicule = Vehicule(**donnees.model_dump())
        vehicule = self.repo.creer(vehicule)
        return self._construire_reponse(vehicule)

    async def creer_admin(
        self,
        donnees: VehiculeCreateAdmin,
        photo_fichier: UploadFile | None = None,
    ) -> VehiculeResponse:
        """Cree un vehicule depuis l'admin (matricule + modele + photo optionnelle)."""
        matricule = donnees.matricule.strip()
        modele = donnees.modele.strip()
        if not matricule or not modele:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="champs_obligatoires",
            )

        existant = self.repo.obtenir_par_matricule(matricule)
        if existant is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="matricule_existant",
            )

        photo_url = ""
        if photo_fichier is not None and photo_fichier.filename:
            photo_url = await enregistrer_photo_vehicule(photo_fichier)

        vehicule = Vehicule(
            matricule=matricule,
            modele=modele,
            marque="",
            photo_url=photo_url,
            date_expiration_itv=date.today() + timedelta(days=365),
            kilometrage_actuel=donnees.kilometrage_actuel,
            consommation_moyenne=Decimal("0.00"),
            utilisateur_assigne=(
                donnees.utilisateur_assigne.strip()
                if donnees.utilisateur_assigne and donnees.utilisateur_assigne.strip()
                else None
            ),
        )
        vehicule = self.repo.creer(vehicule)
        if vehicule.utilisateur_assigne:
            self._synchroniser_journal_assignation(vehicule)
            self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def _synchroniser_journal_assignation(
        self, vehicule: Vehicule, date_reference: date | None = None
    ) -> None:
        """Assure un journal actif pour l'utilisateur assigne permanent."""
        assigne = (vehicule.utilisateur_assigne or "").strip()
        jour = date_reference or date.today()
        if not assigne:
            for journal in obtenir_journaux_du_jour(vehicule, jour):
                journal.actif = False
            return

        for journal in obtenir_journaux_du_jour(vehicule, jour):
            if journal.utilisateur and journal.utilisateur.strip().lower() == assigne.lower():
                journal.actif = True
            else:
                journal.actif = False

        journal_actif = self.repo.obtenir_journal_actif(vehicule.id, jour)
        if journal_actif is None:
            entree = self.repo.obtenir_journal_par_utilisateur(vehicule.id, jour, assigne)
            if entree is not None:
                entree.actif = True
            else:
                self.repo.session.add(
                    VehiculeJournal(
                        vehicule_id=vehicule.id,
                        date_jour=jour,
                        utilisateur=assigne,
                        actif=True,
                        kilometrage_actuel=vehicule.kilometrage_actuel,
                        kilometrage_jour=0,
                        consommation_jour=Decimal("0.00"),
                        cout_carburant_jour=Decimal("0.00"),
                    )
                )

    def _assurer_journal_assignation_jour(
        self, vehicule: Vehicule, date_reference: date | None = None
    ) -> None:
        """Cree le journal du jour pour l'assignation permanente si necessaire."""
        if not (vehicule.utilisateur_assigne or "").strip():
            return
        jour = date_reference or date.today()
        if self.repo.obtenir_journal_actif(vehicule.id, jour) is not None:
            return
        self._synchroniser_journal_assignation(vehicule, jour)
        self.repo.session.flush()

    async def modifier_admin(
        self,
        vehicule_id: int,
        donnees: VehiculeUpdateAdmin,
        photo_fichier: UploadFile | None = None,
    ) -> VehiculeResponse:
        """Modifie matricule, modele, assignation et photo d'un vehicule."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        matricule = donnees.matricule.strip()
        modele = donnees.modele.strip()
        if not matricule or not modele:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="champs_obligatoires",
            )

        autre = self.repo.obtenir_par_matricule(matricule)
        if autre is not None and autre.id != vehicule_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="matricule_existant",
            )

        vehicule.matricule = matricule
        vehicule.modele = modele
        vehicule.utilisateur_assigne = (
            donnees.utilisateur_assigne.strip()
            if donnees.utilisateur_assigne and donnees.utilisateur_assigne.strip()
            else None
        )

        if photo_fichier is not None and photo_fichier.filename:
            ancienne_photo = vehicule.photo_url
            nouvelle_url = await enregistrer_photo_vehicule(photo_fichier)
            vehicule.photo_url = nouvelle_url
            if ancienne_photo:
                supprimer_photo_locale(ancienne_photo)

        vehicule = self.repo.sauvegarder(vehicule)
        self._synchroniser_journal_assignation(vehicule)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def changer_assignation_admin(
        self,
        vehicule_id: int,
        utilisateur_assigne: str | None,
    ) -> VehiculeResponse:
        """Met a jour l'utilisateur assigne permanent d'un vehicule."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        vehicule.utilisateur_assigne = (
            utilisateur_assigne.strip()
            if utilisateur_assigne and utilisateur_assigne.strip()
            else None
        )
        vehicule = self.repo.sauvegarder(vehicule)
        self._synchroniser_journal_assignation(vehicule)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def supprimer_admin(self, vehicule_id: int) -> None:
        """Supprime un vehicule et sa photo locale eventuelle."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        photo_url = vehicule.photo_url
        self.repo.supprimer(vehicule)
        if photo_url:
            supprimer_photo_locale(photo_url)

    def enregistrer_donnees_jour(
        self,
        vehicule_id: int,
        donnees: DonneesJourVehicule,
        utilisateur: Utilisateur,
    ) -> VehiculeJournalResponse:
        """Enregistre ou met a jour les donnees d'une journee."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicule non trouve",
            )

        if est_au_garage(vehicule):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_au_garage",
            )

        journal_actif = self.repo.obtenir_journal_actif(vehicule_id, donnees.date_jour)
        if journal_actif is None:
            self._synchroniser_journal_assignation(vehicule, donnees.date_jour)
            self.repo.session.flush()
            journal_actif = self.repo.obtenir_journal_actif(vehicule_id, donnees.date_jour)
        if journal_actif is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_non_assigne",
            )

        assigne = obtenir_utilisateur_effectif(vehicule, donnees.date_jour) or ""
        if not peut_actualizar_donnees_vehicule(utilisateur, assigne):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="actualisation_non_autorisee",
            )

        journal_actif.consommation_jour = donnees.consommation_jour
        journal_actif.cout_carburant_jour = donnees.cout_carburant_jour
        appliquer_mise_a_jour_kilometrage(
            vehicule, journal_actif, donnees.kilometrage_actuel
        )

        self.repo.sauvegarder(vehicule)
        self.repo.session.refresh(journal_actif)

        return VehiculeJournalResponse.model_validate(journal_actif)

    def modifier_itv(self, vehicule_id: int, donnees: ItvUpdate) -> VehiculeResponse:
        """Met a jour la date d'expiration ITV d'un vehicule."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        vehicule.date_expiration_itv = donnees.date_expiration_itv
        vehicule = self.repo.sauvegarder(vehicule)
        self._synchroniser_journal_assignation(vehicule)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def assigner_vehicule_admin(
        self,
        vehicule_id: int,
        nom_utilisateur: str | None,
    ) -> VehiculeResponse:
        """Assigne durablement un vehicule a un utilisateur (admin)."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        vehicule.utilisateur_assigne = (
            nom_utilisateur.strip() if nom_utilisateur and nom_utilisateur.strip() else None
        )
        vehicule = self.repo.sauvegarder(vehicule)
        self._synchroniser_journal_assignation(vehicule)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def assigner_vehicule(
        self, vehicule_id: int, utilisateur: Utilisateur
    ) -> VehiculeResponse:
        """Assigne le vehicule a l'utilisateur courant pour aujourd'hui."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )
        if est_au_garage(vehicule):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_au_garage",
            )

        jour = date.today()
        if calculer_statut_itv(vehicule.date_expiration_itv, jour) == StatutItv.EXPIREE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="itv_expiree",
            )

        if obtenir_utilisateur_effectif(vehicule, jour):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_deja_occupe",
            )

        nom = obtenir_nom_affichage(utilisateur)
        vehicule.utilisateur_assigne = nom
        vehicule = self.repo.sauvegarder(vehicule)
        self._synchroniser_journal_assignation(vehicule, jour)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def liberer_vehicule(self, vehicule_id: int) -> VehiculeResponse:
        """Libere le vehicule (fin d'utilisation pour aujourd'hui)."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        jour = date.today()
        journal_actif = self.repo.obtenir_journal_actif(vehicule_id, jour)
        if journal_actif is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_deja_libre",
            )

        journal_actif.actif = False
        self.repo.sauvegarder_journal(journal_actif)
        vehicule.utilisateur_assigne = None
        vehicule = self.repo.sauvegarder(vehicule)
        self.repo.session.commit()
        return self._construire_reponse(vehicule)

    def ajouter_journal(
        self,
        vehicule_id: int,
        donnees: VehiculeJournalCreate,
        utilisateur: Utilisateur,
    ) -> VehiculeJournalResponse:
        """Ajoute une entree journaliere via l'API (compatibilite)."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicule non trouve",
            )

        try:
            payload = DonneesJourVehicule(
                date_jour=donnees.date_jour,
                kilometrage_actuel=donnees.kilometrage_actuel,
                consommation_jour=donnees.consommation_jour,
                cout_carburant_jour=donnees.cout_carburant_jour,
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="carburant_incomplet",
            ) from exc

        return self.enregistrer_donnees_jour(vehicule_id, payload, utilisateur)

    def obtenir_garages_connus(self) -> list[str]:
        """Retourne les garages deja saisis pour l'autocompletion."""
        return self.repo.obtenir_garages_connus()

    def mettre_au_garage(
        self,
        vehicule_id: int,
        donnees: ImmobilisationCreate,
        utilisateur: Utilisateur | None = None,
    ) -> ImmobilisationResponse:
        """Immobilise un vehicule au garage."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )
        if est_au_garage(vehicule):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_deja_au_garage",
            )

        jour = date.today()

        if utilisateur is not None and utilisateur.role != "admin":
            self._assurer_journal_assignation_jour(vehicule, jour)
            assigne = obtenir_utilisateur_effectif(vehicule, jour) or ""
            if not peut_actualizar_donnees_vehicule(utilisateur, assigne):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="actualisation_non_autorisee",
                )
        journal_actif = self.repo.obtenir_journal_actif(vehicule_id, jour)
        if journal_actif is not None:
            journal_actif.actif = False

        immobilisation = VehiculeImmobilisation(
            vehicule_id=vehicule.id,
            motif=donnees.motif.value,
            garage=donnees.garage.strip(),
            date_debut=donnees.date_debut,
            date_retour_estimee=donnees.date_retour_estimee,
            commentaire=donnees.commentaire.strip() if donnees.commentaire else None,
        )
        self.repo.ajouter_immobilisation(immobilisation)
        return ImmobilisationResponse.model_validate(immobilisation)

    def remettre_en_service(
        self, vehicule_id: int, donnees: RemiseEnServiceCreate
    ) -> VehiculeResponse:
        """Cloture l'immobilisation et remet le vehicule en service."""
        vehicule = self.repo.obtenir_par_id(vehicule_id)
        if vehicule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="vehicule_introuvable",
            )

        immobilisation = obtenir_immobilisation_active(vehicule)
        if immobilisation is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="vehicule_pas_au_garage",
            )

        date_fin = donnees.date_fin or date.today()
        immobilisation.date_fin = date_fin

        self.repo.sauvegarder_immobilisation(immobilisation)
        return self._construire_reponse(vehicule)

    def rechercher_global(self, terme: str) -> list[ResultatRecherche]:
        """Recherche globale pour la page d'accueil."""
        if not terme.strip():
            return []

        vehicules = self.repo.rechercher(terme)
        resultats: list[ResultatRecherche] = []

        for v in vehicules:
            reponse = self._construire_reponse(v)
            utilisateur = reponse.utilisateur_assigne or reponse.utilisateur_jour or "Libre"
            resultats.append(
                ResultatRecherche(
                    module_id="vehicules",
                    module_libelle="Vehiculos",
                    titre=f"{reponse.modele_affiche} ({v.matricule})",
                    sous_titre=f"Usuario: {utilisateur}",
                    route_web="/vehicules",
                )
            )

        return resultats
