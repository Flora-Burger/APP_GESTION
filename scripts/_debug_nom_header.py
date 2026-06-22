import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from jinja2 import Template

from backend.app.core.dependances import obtenir_traductions

t = obtenir_traductions()
print("nom_utilisateur", repr(t.get("nom_utilisateur")))
print("nom", repr(t.get("nom")))
print("render", Template("{{ t['nom_utilisateur'] }}").render(t=t))
