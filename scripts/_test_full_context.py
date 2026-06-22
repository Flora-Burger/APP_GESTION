"""Simulate full template response path."""
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
    "query_string": b"",
}
request = Request(scope)

ctx = contexte_template(
    request,
    utilisateurs=[],
    message=None,
    erreur=None,
    roles=RoleUtilisateur,
)

print("ctx t nom:", repr(ctx["t"].get("nom")))
print("ctx t type:", type(ctx["t"]))

tpl = templates.env.get_template("admin/users.html")
html = tpl.render(ctx)

m = re.search(r'<label for="nom_utilisateur">([^<]*)</label>', html)
print("rendered label:", repr(m.group(1) if m else "MISSING"))
