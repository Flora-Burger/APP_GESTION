"""Debug TRADUCTIONS nom key via import in subprocess."""
import sys
sys.path.insert(0, "e:/FLORA/APP_GESTION")
from backend.app.traductions.es import TRADUCTIONS
print("nom in TRADUCTIONS:", "nom" in TRADUCTIONS)
print("value:", repr(TRADUCTIONS.get("nom")))
print("bracket render test:")
from backend.app.core.dependances import templates
tpl = templates.env.get_template("admin/users.html")
# minimal slice
src = tpl.environment.loader.get_source(tpl.environment, "admin/users.html")[0]
for line in src.splitlines():
    if "nom_utilisateur" in line or ("nom" in line and "label" in line):
        print(line)
