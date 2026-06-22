"""Dependances FastAPI partagees."""

from fastapi import Request
from fastapi.templating import Jinja2Templates

from backend.app.modules.auth.affichage import obtenir_nom_affichage
from backend.app.modules.base.registre_modules import obtenir_modules_actifs
from backend.app.core.config import RACINE_PROJET, obtenir_parametres
from backend.app.traductions.es import TRADUCTIONS as TRADUCTIONS_ES

templates = Jinja2Templates(directory=str(RACINE_PROJET / "backend" / "app" / "templates"))

# Secours si le module es.py en memoire est ancien (cles nom ajoutees recemment).
_TRADUCTIONS_SECOURS: dict[str, str] = {
    "nom": "Nombre",
    "nom_utilisateur": "Nombre",
    "nom_utilisateur_placeholder": "Ej. Maria",
    "nom_obligatoire": "El nombre es obligatorio",
    "creer_compte_desc": (
        "Indique el identificador, el nombre, la contrasena y el rol del nuevo usuario."
    ),
    "prenom": "Nombre",
    "prenom_placeholder": "Ej. Maria",
    "nom_famille": "Apellido",
    "nom_famille_placeholder": "Ej. Garcia",
    "email_placeholder_compte": "001",
    "mot_de_passe_min": "Minimo 3 caracteres",
    "mot_de_passe_optionnel": "Dejar vacio para mantener la contrasena actual",
    "modifier_compte": "Modificar cuenta",
}


def obtenir_traductions() -> dict[str, str]:
    """Retourne les traductions avec cles de secours pour l'admin comptes."""
    traductions = dict(TRADUCTIONS_ES)
    for cle, valeur in _TRADUCTIONS_SECOURS.items():
        traductions.setdefault(cle, valeur)
    return traductions


def contexte_template(request: Request, **kwargs):
    """Construit le contexte commun pour tous les templates Jinja2."""
    parametres = obtenir_parametres()
    utilisateur = getattr(request.state, "utilisateur", None)
    contexte = {
        "request": request,
        "t": obtenir_traductions(),
        "nom_entreprise": parametres.nom_entreprise,
        "logo_url": parametres.logo_url,
        "utilisateur_courant": utilisateur,
        "nom_utilisateur_courant": obtenir_nom_affichage(utilisateur),
        "est_admin": utilisateur is not None and utilisateur.role == "admin",
        "modules_navigation": obtenir_modules_actifs(),
    }
    contexte.update(kwargs)
    return contexte
