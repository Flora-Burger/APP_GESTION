"""Routes web (Jinja2 + HTMX) pour le module vehicules."""

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.affichage import obtenir_nom_affichage
from backend.app.modules.auth.identifiant import ID_UTILISATEUR_LIBRE, normaliser_identifiant
from backend.app.modules.auth.service import AuthService
from backend.app.modules.vehicules.schemas import (
    DonneesJourVehicule,
    FiltreItv,
    FiltreKmJour,
    FiltreStatut,
    ImmobilisationCreate,
    MotifImmobilisation,
    ItvUpdate,
    RemiseEnServiceCreate,
)
from backend.app.modules.vehicules.configuration_service import ConfigurationVehiculesService
from backend.app.modules.vehicules.service import VehiculeService

router = APIRouter(tags=["vehicules-web"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> VehiculeService:
    return VehiculeService(session)


def _params_filtres(
    recherche: str | None = None,
    statut: str | None = None,
    itv: str | None = None,
    km_jour: str | None = None,
) -> dict:
    """Convertit les parametres de formulaire en enums."""
    return {
        "recherche": recherche or None,
        "statut": FiltreStatut(statut) if statut else None,
        "itv": FiltreItv(itv) if itv else None,
        "km_jour": FiltreKmJour(km_jour) if km_jour else None,
    }


def _contexte_liste(request: Request, vehicules, session: Session | None = None, **extra):
    """Contexte commun pour les fragments de liste."""
    config_flotte = None
    if session is not None:
        config_flotte = ConfigurationVehiculesService(session).obtenir()
    return contexte_template(
        request,
        vehicules=vehicules,
        config_flotte=config_flotte,
        date_aujourdhui=date.today().isoformat(),
        **extra,
    )


def _filtre_assignation(request: Request) -> str | None:
    """Limite la liste au vehicule assigne pour les utilisateurs standards."""
    utilisateur = getattr(request.state, "utilisateur", None)
    if utilisateur is None or utilisateur.role == "admin":
        return None
    return obtenir_nom_affichage(utilisateur)


def _lister_pour_request(
    request: Request,
    service: VehiculeService,
    filtres: dict,
) -> list:
    return service.lister(**filtres, utilisateur_assigne=_filtre_assignation(request))


def _exiger_admin_web(request: Request) -> None:
    """Refuse l'acces si l'utilisateur n'est pas administrateur."""
    utilisateur = getattr(request.state, "utilisateur", None)
    if utilisateur is None or utilisateur.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="acces_refuse")


def _resoudre_utilisateur_assigne(session: Session, utilisateur_id: str) -> str | None:
    """Convertit l'identifiant 3 chiffres en nom affiche (000 = liberer)."""
    if not utilisateur_id or not utilisateur_id.strip():
        return None
    try:
        identifiant = normaliser_identifiant(utilisateur_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="identifiant_invalide") from exc

    if identifiant == ID_UTILISATEUR_LIBRE:
        return None

    utilisateur = AuthService(session).repo.obtenir_par_email(identifiant)
    if utilisateur is None or not utilisateur.est_actif:
        raise HTTPException(status_code=400, detail="utilisateur_introuvable")
    return obtenir_nom_affichage(utilisateur)


@router.get("/vehicules", response_class=HTMLResponse)
def page_vehicules(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    itv: str | None = None,
    km_jour: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Page principale de gestion des vehicules."""
    filtres = _params_filtres(recherche, statut, itv, km_jour)
    vehicules = _lister_pour_request(request, service, filtres)
    config_flotte = ConfigurationVehiculesService(session).obtenir()

    return templates.TemplateResponse(
        request,
        "vehicules/liste.html",
        contexte_template(
            request,
            vehicules=vehicules,
            config_flotte=config_flotte,
            filtres_actifs={
                "recherche": recherche or "",
                "statut": statut or "",
                "itv": itv or "",
                "km_jour": km_jour or "",
            },
            date_aujourdhui=date.today().isoformat(),
            garages_connus=service.obtenir_garages_connus(),
        ),
    )


@router.get("/vehicules/partials/liste", response_class=HTMLResponse)
def partial_liste_vehicules(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    itv: str | None = None,
    km_jour: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Fragment HTMX de la liste des vehicules."""
    filtres = _params_filtres(recherche, statut, itv, km_jour)
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(request, vehicules, session=session),
    )


def _params_filtres_historique(
    recherche_utilisateur: str | None,
    recherche_date: str | None,
) -> tuple[str | None, date | None, dict[str, str]]:
    """Parse les filtres de recherche sur l'historique."""
    utilisateur = (recherche_utilisateur or "").strip() or None
    date_valeur = (recherche_date or "").strip()
    date_filtre = None
    if date_valeur:
        try:
            date_filtre = date.fromisoformat(date_valeur)
        except ValueError:
            date_valeur = ""
    filtres_actifs = {
        "utilisateur": utilisateur or "",
        "date": date_filtre.isoformat() if date_filtre else date_valeur,
    }
    return utilisateur, date_filtre, filtres_actifs


def _contexte_historique(
    request: Request,
    vehicule,
    filtres_historique: dict[str, str],
):
    """Contexte commun pour la page et le fragment d'historique."""
    return contexte_template(
        request,
        vehicule=vehicule,
        filtres_historique=filtres_historique,
    )


@router.get("/vehicules/{vehicule_id}/historique", response_class=HTMLResponse)
def page_historique(
    request: Request,
    vehicule_id: int,
    recherche_utilisateur: str | None = None,
    recherche_date: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Vue historique journalier d'un vehicule."""
    utilisateur, date_filtre, filtres = _params_filtres_historique(
        recherche_utilisateur, recherche_date
    )
    detail = service.obtenir_historique(vehicule_id, utilisateur, date_filtre)

    return templates.TemplateResponse(
        request,
        "vehicules/historique.html",
        _contexte_historique(request, detail, filtres),
    )


@router.get(
    "/vehicules/{vehicule_id}/historique/partials/contenu",
    response_class=HTMLResponse,
)
def partial_historique_contenu(
    request: Request,
    vehicule_id: int,
    recherche_utilisateur: str | None = None,
    recherche_date: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Fragment HTMX de l'historique filtre."""
    utilisateur, date_filtre, filtres = _params_filtres_historique(
        recherche_utilisateur, recherche_date
    )
    detail = service.obtenir_historique(vehicule_id, utilisateur, date_filtre)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/historique_contenu.html",
        _contexte_historique(request, detail, filtres),
    )


def _parser_kilometrage_form(valeur: str) -> int:
    """Convertit une saisie formulaire en kilometrage entier."""
    try:
        texte = (valeur or "").strip().replace(",", ".")
        if not texte:
            return 0
        return max(0, int(float(texte)))
    except (TypeError, ValueError):
        return 0


@router.post("/vehicules/{vehicule_id}/journal", response_class=HTMLResponse)
def enregistrer_journal(
    request: Request,
    vehicule_id: int,
    date_jour: str = Form(...),
    kilometrage_actuel_saisi: str = Form(...),
    consommation_jour: str = Form(default="0"),
    cout_carburant_jour: str = Form(default="0"),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Enregistre les donnees du jour depuis le formulaire web."""
    message_erreur = None
    message_succes = None

    try:
        conso = Decimal(consommation_jour.replace(",", "."))
    except (InvalidOperation, AttributeError):
        conso = Decimal("0")

    try:
        cout = Decimal(cout_carburant_jour.replace(",", "."))
    except (InvalidOperation, AttributeError):
        cout = Decimal("0")

    try:
        donnees = DonneesJourVehicule(
            date_jour=date.fromisoformat(date_jour),
            kilometrage_actuel=_parser_kilometrage_form(kilometrage_actuel_saisi),
            consommation_jour=conso,
            cout_carburant_jour=cout,
        )
        service.enregistrer_donnees_jour(vehicule_id, donnees, request.state.utilisateur)
        message_succes = "journal_enregistre"
    except ValidationError:
        message_erreur = "erreur_carburant_lie"
    except HTTPException as exc:
        if exc.detail == "carburant_incomplet":
            message_erreur = "erreur_carburant_lie"
        elif exc.detail == "vehicule_au_garage":
            message_erreur = "erreur_vehicule_au_garage"
        elif exc.detail == "vehicule_non_assigne":
            message_erreur = "erreur_vehicule_non_assigne"
        elif exc.detail == "actualisation_non_autorisee":
            message_erreur = "erreur_actualisation_non_autorisee"
        elif exc.detail == "kilometrage_invalide":
            message_erreur = "erreur_kilometrage_invalide"
        else:
            message_erreur = "erreur_journal"
    except ValueError:
        message_erreur = "erreur_journal"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            session=session,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/itv", response_class=HTMLResponse)
def modifier_itv(
    request: Request,
    vehicule_id: int,
    date_expiration_itv: str = Form(...),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Met a jour la date ITV depuis la modal web."""
    message_erreur = None
    message_succes = None

    try:
        donnees = ItvUpdate(date_expiration_itv=date.fromisoformat(date_expiration_itv))
        service.modifier_itv(vehicule_id, donnees)
        message_succes = "itv_modifiee"
    except ValidationError:
        message_erreur = "erreur_itv"
    except HTTPException as exc:
        if exc.detail == "vehicule_introuvable":
            message_erreur = "erreur_itv"
        else:
            message_erreur = "erreur_itv"
    except ValueError:
        message_erreur = "erreur_itv"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            session=session,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/garage", response_class=HTMLResponse)
def mettre_au_garage(
    request: Request,
    vehicule_id: int,
    motif: str = Form(...),
    garage: str = Form(...),
    date_debut: str = Form(...),
    date_retour_estimee: str = Form(default=""),
    commentaire: str = Form(default=""),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Immobilise un vehicule depuis la modal web."""
    message_erreur = None
    message_succes = None

    try:
        donnees = ImmobilisationCreate(
            motif=MotifImmobilisation(motif),
            garage=garage.strip(),
            date_debut=date.fromisoformat(date_debut),
            date_retour_estimee=(
                date.fromisoformat(date_retour_estimee) if date_retour_estimee else None
            ),
            commentaire=commentaire.strip() or None,
        )
        service.mettre_au_garage(
            vehicule_id,
            donnees,
            getattr(request.state, "utilisateur", None),
        )
        message_succes = "vehicule_mis_au_garage"
    except ValidationError:
        message_erreur = "erreur_immobilisation"
    except HTTPException as exc:
        if exc.detail == "vehicule_deja_au_garage":
            message_erreur = "erreur_vehicule_deja_au_garage"
        elif exc.detail == "actualisation_non_autorisee":
            message_erreur = "erreur_actualisation_non_autorisee"
        else:
            message_erreur = "erreur_immobilisation"
    except ValueError:
        message_erreur = "erreur_immobilisation"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            session=session,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/remettre-en-service", response_class=HTMLResponse)
def remettre_en_service(
    request: Request,
    vehicule_id: int,
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Remet un vehicule en service depuis la modal web."""
    message_erreur = None
    message_succes = None

    try:
        donnees = RemiseEnServiceCreate(date_fin=date.today())
        service.remettre_en_service(vehicule_id, donnees)
        message_succes = "vehicule_remis_en_service"
    except ValidationError:
        message_erreur = "erreur_remise_en_service"
    except HTTPException as exc:
        if exc.detail == "vehicule_pas_au_garage":
            message_erreur = "erreur_vehicule_pas_au_garage"
        else:
            message_erreur = "erreur_remise_en_service"
    except ValueError:
        message_erreur = "erreur_remise_en_service"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            session=session,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/assignation", response_class=HTMLResponse)
def modifier_assignation_vehicule(
    request: Request,
    vehicule_id: int,
    utilisateur_id: str = Form(default=""),
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    """Change l'utilisateur assigne depuis la fiche vehicule (admin)."""
    message_erreur = None
    message_succes = None

    try:
        _exiger_admin_web(request)
        nom_assigne = _resoudre_utilisateur_assigne(session, utilisateur_id)
        service.changer_assignation_admin(vehicule_id, nom_assigne)
        message_succes = (
            "vehicule_libere"
            if nom_assigne is None and utilisateur_id.strip()
            else "assignation_modifiee"
        )
    except HTTPException as exc:
        if exc.detail == "acces_refuse":
            message_erreur = "erreur_acces_refuse"
        elif exc.detail == "identifiant_invalide":
            message_erreur = "identifiant_invalide"
        elif exc.detail == "utilisateur_introuvable":
            message_erreur = "utilisateur_introuvable"
        elif exc.detail == "vehicule_introuvable":
            message_erreur = "vehicule_introuvable"
        else:
            message_erreur = "erreur_assignation"
    except ValueError:
        message_erreur = "erreur_assignation"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = _lister_pour_request(request, service, filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            session=session,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )
