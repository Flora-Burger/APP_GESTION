"""Routes web d'administration des vehicules (admin uniquement)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.admin_web import verifier_admin_web
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.affichage import obtenir_nom_affichage
from backend.app.modules.auth.identifiant import ID_UTILISATEUR_LIBRE, normaliser_identifiant
from backend.app.modules.auth.service import AuthService
from backend.app.modules.vehicules.configuration_service import ConfigurationVehiculesService
from backend.app.modules.vehicules.donnees_json import ContactoSeguro, TallerReferencia
from backend.app.modules.vehicules.schemas import (
    ConfigurationVehiculesUpdate,
    VehiculeCreateAdmin,
    VehiculeUpdateAdmin,
)
from backend.app.modules.vehicules.service import VehiculeService

router = APIRouter(tags=["admin-vehicules"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> VehiculeService:
    return VehiculeService(session)


def _obtenir_config_service(session: Session = Depends(obtenir_session)) -> ConfigurationVehiculesService:
    return ConfigurationVehiculesService(session)


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


def _identifiant_depuis_nom(session: Session, nom: str | None) -> str:
    if not nom or not nom.strip():
        return ""
    cible = nom.strip()
    for utilisateur in AuthService(session).lister_utilisateurs():
        if obtenir_nom_affichage(utilisateur) == cible:
            return utilisateur.email
    return ""


def _parser_contactos_formulaire(
    etiquetas: list[str] | None = None,
    telefonos: list[str] | None = None,
) -> list[ContactoSeguro]:
    etiquettes = etiquetas or []
    tels = telefonos or []
    total = max(len(etiquettes), len(tels), 0)
    contactos: list[ContactoSeguro] = []
    for index in range(total):
        etiqueta = etiquettes[index].strip() if index < len(etiquettes) else ""
        telefono = tels[index].strip() if index < len(tels) else ""
        if etiqueta or telefono:
            contactos.append(ContactoSeguro(etiqueta=etiqueta, telefono=telefono))
    return contactos


def _parser_talleres_formulaire(
    ciudades: list[str] | None = None,
    noms: list[str] | None = None,
    telefonos: list[str] | None = None,
    direcciones: list[str] | None = None,
) -> list[TallerReferencia]:
    ciudades = ciudades or []
    noms = noms or []
    telefonos = telefonos or []
    direcciones = direcciones or []
    total = max(len(ciudades), len(noms), len(telefonos), len(direcciones), 0)
    talleres: list[TallerReferencia] = []
    for index in range(total):
        ciudad = ciudades[index].strip() if index < len(ciudades) else ""
        nom = noms[index].strip() if index < len(noms) else ""
        tel = telefonos[index].strip() if index < len(telefonos) else ""
        dir_ = direcciones[index].strip() if index < len(direcciones) else ""
        if ciudad or nom or tel or dir_:
            talleres.append(
                TallerReferencia(ciudad=ciudad, nombre=nom, telefono=tel, direccion=dir_)
            )
    return talleres


@router.get("/admin/vehicules", response_class=HTMLResponse)
def page_admin_vehicules(
    request: Request,
    recherche: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    vehicules = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/vehicules.html",
        contexte_template(
            request,
            vehicules=vehicules,
            filtres_actifs={"recherche": recherche or ""},
            message=message,
            erreur=erreur,
        ),
    )


@router.get("/admin/vehicules/configuracion", response_class=HTMLResponse)
def page_configuration_vehicules(
    request: Request,
    config_service: ConfigurationVehiculesService = Depends(_obtenir_config_service),
    message: str | None = None,
    erreur: str | None = None,
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    config = config_service.obtenir()

    return templates.TemplateResponse(
        request,
        "admin/vehicules_configuracion.html",
        contexte_template(
            request,
            config=config,
            message=message,
            erreur=erreur,
        ),
    )


@router.post("/admin/vehicules/configuracion")
def enregistrer_configuration_vehicules(
    request: Request,
    contacto_etiqueta: list[str] = Form(default=[]),
    contacto_telefono: list[str] = Form(default=[]),
    taller_ciudad: list[str] = Form(default=[]),
    taller_nombre: list[str] = Form(default=[]),
    taller_telefono: list[str] = Form(default=[]),
    taller_direccion: list[str] = Form(default=[]),
    config_service: ConfigurationVehiculesService = Depends(_obtenir_config_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    existant = config_service.obtenir()
    donnees = ConfigurationVehiculesUpdate(
        seguro_compania=existant.seguro_compania,
        seguro_poliza=existant.seguro_poliza,
    )
    contactos = _parser_contactos_formulaire(contacto_etiqueta, contacto_telefono)
    talleres = _parser_talleres_formulaire(
        taller_ciudad, taller_nombre, taller_telefono, taller_direccion
    )
    config_service.modifier(donnees, contactos, talleres)
    return RedirectResponse(
        url="/admin/vehicules/configuracion?message=config_vehicules_modifiee",
        status_code=303,
    )


@router.get("/admin/vehicules/partials/liste", response_class=HTMLResponse)
def partial_liste_admin_vehicules(
    request: Request,
    recherche: str | None = None,
    service: VehiculeService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    vehicules = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/partials/vehicules_table.html",
        contexte_template(request, vehicules=vehicules),
    )


@router.post("/admin/vehicules")
async def creer_vehicule_admin(
    request: Request,
    matricule: str = Form(...),
    modele: str = Form(...),
    kilometrage_actuel: str = Form(...),
    utilisateur_id: str = Form(default=""),
    photo: UploadFile | None = File(None),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        km = int(kilometrage_actuel.strip())
        if km < 0:
            raise ValueError
        nom_assigne = _resoudre_utilisateur_assigne(session, utilisateur_id)
        donnees = VehiculeCreateAdmin(
            matricule=matricule,
            modele=modele,
            kilometrage_actuel=km,
            utilisateur_assigne=nom_assigne,
        )
        await service.creer_admin(donnees, photo)
        return RedirectResponse(url="/admin/vehicules?message=vehicule_cree", status_code=303)
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/admin/vehicules?erreur=erreur_kilometrage_invalide",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_creation_vehicule"
        if detail in {"identifiant_invalide", "utilisateur_introuvable"}:
            return RedirectResponse(url=f"/admin/vehicules?erreur={detail}", status_code=303)
        erreurs_connues = {
            "matricule_existant",
            "photo_invalide",
            "photo_format_invalide",
            "photo_trop_volumineuse",
            "erreur_kilometrage_invalide",
            "erreur_stockage_blob",
        }
        erreur = detail if detail in erreurs_connues else "erreur_creation_vehicule"
        return RedirectResponse(url=f"/admin/vehicules?erreur={erreur}", status_code=303)


@router.get("/admin/vehicules/{vehicule_id}/modifier", response_class=HTMLResponse)
def page_modifier_vehicule(
    request: Request,
    vehicule_id: int,
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
    message: str | None = None,
    erreur: str | None = None,
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        vehicule = service.obtenir_detail(vehicule_id)
    except HTTPException:
        return RedirectResponse(url="/admin/vehicules?erreur=vehicule_introuvable", status_code=303)

    utilisateur_assigne_id = _identifiant_depuis_nom(session, vehicule.utilisateur_assigne)

    return templates.TemplateResponse(
        request,
        "admin/vehicule_modifier.html",
        contexte_template(
            request,
            vehicule=vehicule,
            utilisateur_assigne_id=utilisateur_assigne_id,
            message=message,
            erreur=erreur,
        ),
    )


@router.post("/admin/vehicules/{vehicule_id}/modifier")
async def modifier_vehicule_admin(
    request: Request,
    vehicule_id: int,
    matricule: str = Form(...),
    modele: str = Form(...),
    utilisateur_id: str = Form(default=""),
    photo: UploadFile | None = File(None),
    service: VehiculeService = Depends(_obtenir_service),
    session: Session = Depends(obtenir_session),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        nom_assigne = _resoudre_utilisateur_assigne(session, utilisateur_id)
        donnees = VehiculeUpdateAdmin(
            matricule=matricule,
            modele=modele,
            utilisateur_assigne=nom_assigne,
        )
        await service.modifier_admin(vehicule_id, donnees, photo)
        return RedirectResponse(
            url=f"/admin/vehicules/{vehicule_id}/modifier?message=vehicule_modifie",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_modification_vehicule"
        erreurs_connues = {
            "matricule_existant",
            "vehicule_introuvable",
            "photo_invalide",
            "photo_format_invalide",
            "photo_trop_volumineuse",
            "erreur_stockage_blob",
            "identifiant_invalide",
            "utilisateur_introuvable",
        }
        erreur = detail if detail in erreurs_connues else "erreur_modification_vehicule"
        return RedirectResponse(
            url=f"/admin/vehicules/{vehicule_id}/modifier?erreur={erreur}",
            status_code=303,
        )


@router.post("/admin/vehicules/{vehicule_id}/supprimer")
def supprimer_vehicule_admin(
    request: Request,
    vehicule_id: int,
    service: VehiculeService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.supprimer_admin(vehicule_id)
        return RedirectResponse(url="/admin/vehicules?message=vehicule_supprime", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_suppression_vehicule"
        erreur = detail if detail == "vehicule_introuvable" else "erreur_suppression_vehicule"
        return RedirectResponse(url=f"/admin/vehicules?erreur={erreur}", status_code=303)
