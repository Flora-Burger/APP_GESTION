"""Helpers d'affichage pour les utilisateurs."""

import re

from fastapi import Request

from backend.app.modules.auth.modeles import Utilisateur

_MOBILE_UA_PATTERN = re.compile(
    r"Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile",
    re.IGNORECASE,
)


def separer_nom_complet(nom: str | None) -> tuple[str, str]:
    """Separe le nom affiche en prenom et nom de famille."""
    if not nom or not nom.strip():
        return "", ""
    parties = nom.strip().split(" ", 1)
    if len(parties) == 1:
        return parties[0], ""
    return parties[0], parties[1]


def normaliser_nom_saisi(nom: str | None) -> str | None:
    """Normalise le nom saisi dans les formulaires admin."""
    if nom is None:
        return None
    valeur = nom.strip()
    return valeur or None


def extraire_nom_formulaire(
    nom: str | None = None,
    prenom: str | None = None,
    nom_famille: str | None = None,
) -> str | None:
    """Lit le nom depuis les champs actuels ou legacy des formulaires admin."""
    direct = normaliser_nom_saisi(nom) or normaliser_nom_saisi(prenom)
    if direct:
        return direct
    return construire_nom_complet(prenom, nom_famille)


def construire_nom_complet(prenom: str | None, nom_famille: str | None) -> str | None:
    """Assemble le nom affiche a partir du prenom et du nom de famille."""
    parties = [partie.strip() for partie in (prenom, nom_famille) if partie and partie.strip()]
    if not parties:
        return None
    return " ".join(parties)


def normaliser_role(role) -> str:
    """Retourne le role sous forme 'admin' ou 'user'."""
    if hasattr(role, "value"):
        return str(role.value).lower()
    valeur = str(role).strip()
    if valeur.startswith("RoleUtilisateur."):
        return valeur.rsplit(".", 1)[-1].lower()
    return valeur.lower()


def parser_role_utilisateur(role: str):
    """Convertit une valeur de formulaire en RoleUtilisateur."""
    from backend.app.modules.auth.schemas import RoleUtilisateur

    return RoleUtilisateur(normaliser_role(role))


def preparer_utilisateurs_affichage(utilisateurs) -> list[dict]:
    """Prepare les champs d'affichage pour la liste admin des comptes."""
    lignes = []
    for utilisateur in utilisateurs:
        nom = (utilisateur.nom or "").strip()
        role = normaliser_role(utilisateur.role)
        lignes.append(
            {
                "id": utilisateur.id,
                "email": utilisateur.email,
                "nom": nom,
                "telefono": (utilisateur.telefono or "").strip(),
                "correo": (utilisateur.correo or "").strip(),
                "role": role,
                "est_actif": utilisateur.est_actif,
                "est_admin": role == "admin",
            }
        )
    return lignes


def obtenir_nom_affichage(utilisateur: Utilisateur | None) -> str:
    """Retourne le nom affiche (nom ou email)."""
    if utilisateur is None:
        return ""
    if utilisateur.nom and utilisateur.nom.strip():
        return utilisateur.nom.strip()
    return utilisateur.email


def est_administrateur(utilisateur: Utilisateur | None) -> bool:
    """True si l'utilisateur connecte est administrateur."""
    if utilisateur is None:
        return False
    return normaliser_role(utilisateur.role) == "admin"


def peut_enregistrer_evenement(utilisateur: Utilisateur | None) -> bool:
    """Seul l'admin peut enregistrer des evenements materiel."""
    return est_administrateur(utilisateur)


def peut_modifier_ressource(utilisateur: Utilisateur | None) -> bool:
    """Seul l'admin peut modifier les ressources (hors journal vehicule assigne)."""
    return est_administrateur(utilisateur)


def peut_actualizar_donnees_vehicule(
    utilisateur: Utilisateur | None,
    utilisateur_assigne: str | None,
) -> bool:
    """True si administrateur ou utilisateur assigne au vehicule."""
    if utilisateur is None:
        return False
    if utilisateur.role == "admin":
        return True
    if not utilisateur_assigne or not utilisateur_assigne.strip():
        return False
    return (
        obtenir_nom_affichage(utilisateur).strip().lower()
        == utilisateur_assigne.strip().lower()
    )


def est_requete_mobile(request: Request) -> bool:
    """Detecte une navigation depuis un appareil mobile."""
    if request.headers.get("sec-ch-ua-mobile") == "?1":
        return True
    user_agent = request.headers.get("user-agent", "")
    return bool(_MOBILE_UA_PATTERN.search(user_agent))


def doit_rediriger_accueil_vers_vehicules(
    utilisateur: Utilisateur | None, request: Request
) -> bool:
    """True si l'employe mobile ne doit pas voir la page d'accueil."""
    return (
        utilisateur is not None
        and not est_administrateur(utilisateur)
        and est_requete_mobile(request)
    )


def obtenir_destination_apres_connexion(
    utilisateur: Utilisateur, request: Request
) -> str:
    """URL de redirection apres login selon le role et l'appareil."""
    if doit_rediriger_accueil_vers_vehicules(utilisateur, request):
        return "/vehicules"
    return "/"
