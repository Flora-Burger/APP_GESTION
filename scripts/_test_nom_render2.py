"""Render users.html with realistic context."""
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

import re
from jinja2 import Environment, FileSystemLoader

from backend.app.traductions.es import TRADUCTIONS
from backend.app.modules.auth.schemas import RoleUtilisateur, UtilisateurResponse
from datetime import datetime

env = Environment(loader=FileSystemLoader("backend/app/templates"))
tpl = env.get_template("admin/users.html")

users = [
    UtilisateurResponse(
        id=1,
        email="a@test.com",
        nom="Alice",
        role=RoleUtilisateur.USER,
        est_actif=True,
        date_creation=datetime.now(),
    )
]

html = tpl.render(
    request=None,
    t=TRADUCTIONS,
    nom_entreprise="X",
    logo_url="",
    utilisateur_courant=users[0],
    nom_utilisateur_courant="Alice",
    est_admin=True,
    utilisateurs=users,
    message=None,
    erreur=None,
    roles=RoleUtilisateur,
)

for field in ("email", "nom", "mot_de_passe", "role"):
    m = re.search(rf'<label for="{field}">([^<]*)</label>', html)
    print(f"label {field}:", repr(m.group(1) if m else "MISSING"))
