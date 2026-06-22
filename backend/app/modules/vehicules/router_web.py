"""Routes web (Jinja2 + HTMX) pour le module vehicules."""

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
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


def _contexte_liste(request: Request, vehicules, **extra):
    """Contexte commun pour les fragments de liste."""
    return contexte_template(
        request,
        vehicules=vehicules,
        date_aujourdhui=date.today().isoformat(),
        **extra,
    )


@router.get("/vehicules", response_class=HTMLResponse)
def page_vehicules(
    request: Request,
    recherche: str | None = None,
    statut: str | None = None,
    itv: str | None = None,
    km_jour: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
):
    """Page principale de gestion des vehicules."""
    filtres = _params_filtres(recherche, statut, itv, km_jour)
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/liste.html",
        contexte_template(
            request,
            vehicules=vehicules,
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
):
    """Fragment HTMX de la liste des vehicules."""
    filtres = _params_filtres(recherche, statut, itv, km_jour)
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(request, vehicules),
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
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
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
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/assigner", response_class=HTMLResponse)
def assigner_vehicule(
    request: Request,
    vehicule_id: int,
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Assigne le vehicule a l'utilisateur connecte."""
    message_erreur = None
    message_succes = None
    utilisateur = getattr(request.state, "utilisateur", None)

    try:
        if utilisateur is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        service.assigner_vehicule(vehicule_id, utilisateur)
        message_succes = "vehicule_assigne"
    except HTTPException as exc:
        if exc.detail == "vehicule_deja_occupe":
            message_erreur = "erreur_vehicule_deja_occupe"
        elif exc.detail == "vehicule_au_garage":
            message_erreur = "erreur_vehicule_au_garage"
        elif exc.detail == "itv_expiree":
            message_erreur = "erreur_itv_expiree"
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
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )


@router.post("/vehicules/{vehicule_id}/liberer", response_class=HTMLResponse)
def liberer_vehicule(
    request: Request,
    vehicule_id: int,
    recherche: str = Form(default=""),
    statut: str = Form(default=""),
    itv: str = Form(default=""),
    km_jour: str = Form(default=""),
    service: VehiculeService = Depends(_obtenir_service),
):
    """Libere le vehicule (fin d'utilisation)."""
    message_erreur = None
    message_succes = None

    try:
        service.liberer_vehicule(vehicule_id)
        message_succes = "vehicule_libere"
    except HTTPException as exc:
        if exc.detail == "vehicule_deja_libre":
            message_erreur = "erreur_vehicule_deja_libre"
        else:
            message_erreur = "erreur_liberation"
    except ValueError:
        message_erreur = "erreur_liberation"

    filtres = _params_filtres(
        recherche or None,
        statut or None,
        itv or None,
        km_jour or None,
    )
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
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
        service.mettre_au_garage(vehicule_id, donnees)
        message_succes = "vehicule_mis_au_garage"
    except ValidationError:
        message_erreur = "erreur_immobilisation"
    except HTTPException as exc:
        if exc.detail == "vehicule_deja_au_garage":
            message_erreur = "erreur_vehicule_deja_au_garage"
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
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
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
    vehicules = service.lister(**filtres)

    return templates.TemplateResponse(
        request,
        "vehicules/partials/liste_cartes.html",
        _contexte_liste(
            request,
            vehicules,
            message_succes=message_succes,
            message_erreur=message_erreur,
        ),
    )
