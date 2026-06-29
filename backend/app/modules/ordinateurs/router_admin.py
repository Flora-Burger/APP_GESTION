"""Routes web d'administration des ordinateurs (admin uniquement)."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.admin_web import verifier_admin_web
from backend.app.core.database import obtenir_session
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.ordinateurs.donnees_json import LicenceLogiciel
from backend.app.modules.ordinateurs.schemas import OrdinateurCreate, OrdinateurUpdate, StatutOrdinateur
from backend.app.modules.ordinateurs.service import OrdinateurService

router = APIRouter(tags=["admin-ordinateurs"])


def _obtenir_service(session: Session = Depends(obtenir_session)) -> OrdinateurService:
    return OrdinateurService(session)


def _parse_date(valeur: str) -> date | None:
    if not valeur or not valeur.strip():
        return None
    return date.fromisoformat(valeur.strip())


def _parser_licences_formulaire(
    licence_nom: list[str] | None = None,
    licence_expiration: list[str] | None = None,
) -> list[LicenceLogiciel]:
    noms = licence_nom or []
    expirations = licence_expiration or []
    licences: list[LicenceLogiciel] = []
    for i, nom in enumerate(noms):
        nom_net = (nom or "").strip()
        if not nom_net:
            continue
        exp = expirations[i].strip() if i < len(expirations) and expirations[i] else None
        licences.append(LicenceLogiciel(nom=nom_net, expiration=exp or None))
    return licences


@router.get("/admin/ordinateurs", response_class=HTMLResponse)
def page_admin_ordinateurs(
    request: Request,
    recherche: str | None = None,
    service: OrdinateurService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    ordinateurs = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/ordinateurs.html",
        contexte_template(
            request,
            ordinateurs=ordinateurs,
            filtres_actifs={"recherche": recherche or ""},
            message=message,
            erreur=erreur,
            statuts=StatutOrdinateur,
        ),
    )


@router.get("/admin/ordinateurs/partials/liste", response_class=HTMLResponse)
def partial_liste_admin_ordinateurs(
    request: Request,
    recherche: str | None = None,
    service: OrdinateurService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    ordinateurs = service.lister(recherche=recherche or None)

    return templates.TemplateResponse(
        request,
        "admin/partials/ordinateurs_table.html",
        contexte_template(request, ordinateurs=ordinateurs),
    )


@router.post("/admin/ordinateurs")
def creer_ordinateur_admin(
    request: Request,
    nom: str = Form(...),
    numero_serie: str = Form(default=""),
    marque: str = Form(...),
    modele: str = Form(...),
    utilisateur_assigne: str = Form(default=""),
    localisation: str = Form(...),
    systeme_exploitation: str = Form(default=""),
    processeur: str = Form(default=""),
    memoire_ram: str = Form(default=""),
    capacite_stockage: str = Form(default=""),
    date_acquisition: str = Form(default=""),
    garantie: str = Form(default=""),
    service: OrdinateurService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        donnees = OrdinateurCreate(
            nom=nom,
            numero_serie=numero_serie or None,
            marque=marque,
            modele=modele,
            utilisateur_assigne=utilisateur_assigne or None,
            localisation=localisation,
            systeme_exploitation=systeme_exploitation or None,
            processeur=processeur or None,
            memoire_ram=memoire_ram or None,
            capacite_stockage=capacite_stockage or None,
            date_acquisition=_parse_date(date_acquisition),
            garantie=garantie or None,
        )
        service.creer_admin(donnees)
        return RedirectResponse(url="/admin/ordinateurs?message=ordinateur_cree", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_creation_ordinateur"
        erreurs_connues = {"nom_existant", "numero_serie_existant"}
        erreur = detail if detail in erreurs_connues else "erreur_creation_ordinateur"
        return RedirectResponse(url=f"/admin/ordinateurs?erreur={erreur}", status_code=303)


@router.get("/admin/ordinateurs/{ordinateur_id}/modifier", response_class=HTMLResponse)
def page_modifier_ordinateur(
    request: Request,
    ordinateur_id: int,
    service: OrdinateurService = Depends(_obtenir_service),
    message: str | None = None,
    erreur: str | None = None,
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        ordinateur = service.obtenir_detail(ordinateur_id)
    except HTTPException:
        return RedirectResponse(url="/admin/ordinateurs?erreur=ordinateur_introuvable", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/ordinateur_modifier.html",
        contexte_template(
            request,
            ordinateur=ordinateur,
            message=message,
            erreur=erreur,
            statuts=StatutOrdinateur,
        ),
    )


@router.post("/admin/ordinateurs/{ordinateur_id}/modifier")
async def modifier_ordinateur_admin(
    request: Request,
    ordinateur_id: int,
    nom: str = Form(...),
    numero_serie: str = Form(default=""),
    marque: str = Form(...),
    modele: str = Form(...),
    utilisateur_assigne: str = Form(default=""),
    localisation: str = Form(...),
    systeme_exploitation: str = Form(default=""),
    processeur: str = Form(default=""),
    memoire_ram: str = Form(default=""),
    capacite_stockage: str = Form(default=""),
    date_acquisition: str = Form(default=""),
    garantie: str = Form(default=""),
    licence_nom: list[str] = Form(default=[]),
    licence_expiration: list[str] = Form(default=[]),
    facture: UploadFile | None = File(default=None),
    service: OrdinateurService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        donnees = OrdinateurUpdate(
            nom=nom,
            numero_serie=numero_serie or None,
            marque=marque,
            modele=modele,
            utilisateur_assigne=utilisateur_assigne or None,
            localisation=localisation,
            systeme_exploitation=systeme_exploitation or None,
            processeur=processeur,
            memoire_ram=memoire_ram or None,
            capacite_stockage=capacite_stockage or None,
            date_acquisition=_parse_date(date_acquisition),
            garantie=garantie or None,
        )
        licences = _parser_licences_formulaire(licence_nom, licence_expiration)
        await service.modifier_avec_facture(ordinateur_id, donnees, facture, licences=licences)
        return RedirectResponse(
            url=f"/admin/ordinateurs/{ordinateur_id}/modifier?message=ordinateur_modifie",
            status_code=303,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_modification_ordinateur"
        erreurs_connues = {
            "nom_existant",
            "numero_serie_existant",
            "ordinateur_introuvable",
            "fichier_invalide",
            "fichier_trop_volumineux",
        }
        erreur = detail if detail in erreurs_connues else "erreur_modification_ordinateur"
        return RedirectResponse(
            url=f"/admin/ordinateurs/{ordinateur_id}/modifier?erreur={erreur}",
            status_code=303,
        )


@router.post("/admin/ordinateurs/{ordinateur_id}/statut")
def modifier_statut_ordinateur_admin(
    request: Request,
    ordinateur_id: int,
    statut: str = Form(...),
    retour: str = Form(default=""),
    service: OrdinateurService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.modifier_statut(ordinateur_id, StatutOrdinateur(statut))
        if retour == "liste":
            return RedirectResponse(url="/ordinateurs?message=statut_ordinateur_modifie", status_code=303)
        return RedirectResponse(
            url=f"/admin/ordinateurs/{ordinateur_id}/modifier?message=statut_ordinateur_modifie",
            status_code=303,
        )
    except (ValueError, HTTPException):
        return RedirectResponse(
            url=f"/admin/ordinateurs/{ordinateur_id}/modifier?erreur=erreur_modification_ordinateur",
            status_code=303,
        )


@router.post("/admin/ordinateurs/{ordinateur_id}/supprimer")
def supprimer_ordinateur_admin(
    request: Request,
    ordinateur_id: int,
    service: OrdinateurService = Depends(_obtenir_service),
):
    redirection = verifier_admin_web(request)
    if redirection:
        return redirection

    try:
        service.supprimer(ordinateur_id)
        return RedirectResponse(url="/admin/ordinateurs?message=ordinateur_supprime", status_code=303)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "erreur_suppression_ordinateur"
        erreur = detail if detail == "ordinateur_introuvable" else "erreur_suppression_ordinateur"
        return RedirectResponse(url=f"/admin/ordinateurs?erreur={erreur}", status_code=303)
