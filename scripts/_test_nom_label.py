"""Test rendu libelle nom formulaire admin."""
from jinja2 import Environment, FileSystemLoader

from backend.app.traductions.es import TRADUCTIONS
from backend.app.modules.auth.schemas import RoleUtilisateur

env = Environment(loader=FileSystemLoader("backend/app/templates"))
tpl = env.get_template("admin/users.html")
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
    roles=RoleUtilisateur,
)

marker = 'for="nom"'
idx = html.find(marker)
if idx < 0:
    print("label nom NOT FOUND")
else:
    snippet = html[idx - 20 : idx + 80]
    print("SNIPPET:", repr(snippet))

print("t['nom']:", repr(TRADUCTIONS.get("nom")))
print("t.nom via jinja:", Environment().from_string("{{ t.nom }}").render(t=TRADUCTIONS))
