"""Render with same Jinja env as the app."""
import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from backend.app.core.dependances import templates
from backend.app.traductions.es import TRADUCTIONS

tpl = templates.env.get_template("admin/users.html")
html = tpl.render(
    request=None,
    t=TRADUCTIONS,
    nom_entreprise="X",
    logo_url="",
    utilisateur_courant=None,
    nom_utilisateur_courant="",
    est_admin=True,
    utilisateurs=[],
    message=None,
    erreur=None,
    roles=None,
)

for field in ("email", "nom", "mot_de_passe", "role"):
    m = re.search(rf'<label for="{field}">([^<]*)</label>', html)
    print(f"label {field}:", repr(m.group(1) if m else "MISSING"))
