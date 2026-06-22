"""Test t[erreur] and t['nom'] with erreur query param."""
import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from starlette.requests import Request
from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.schemas import RoleUtilisateur

scope = {
    "type": "http",
    "method": "GET",
    "path": "/admin/users",
    "headers": [],
    "query_string": b"erreur=nom_obligatoire",
}
request = Request(scope)

ctx = contexte_template(
    request,
    utilisateurs=[],
    message=None,
    erreur="nom_obligatoire",
    roles=RoleUtilisateur,
)

print("t nom:", repr(ctx["t"].get("nom")))
print("t nom_obligatoire:", repr(ctx["t"].get("nom_obligatoire")))
print("erreur:", repr(ctx["erreur"]))

tpl = templates.env.get_template("admin/users.html")
html = tpl.render(ctx)

m = re.search(r'message-erreur">([^<]*)</div>', html)
print("error div:", repr(m.group(1) if m else "MISSING"))

m2 = re.search(r'<label for="nom_utilisateur">([^<]*)</label>', html)
print("nom label:", repr(m2.group(1) if m2 else "MISSING"))
