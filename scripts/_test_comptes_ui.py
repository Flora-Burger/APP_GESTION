import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from backend.app.core.dependances import contexte_template, templates
from starlette.requests import Request

scope = {"type": "http", "method": "GET", "path": "/admin/users", "headers": [], "query_string": b""}
request = Request(scope)
ctx = contexte_template(request, utilisateurs=[], message=None, erreur=None)

html = templates.env.get_template("admin/users.html").render(ctx)
assert "carte-compte-admin" in html
assert "Nombre del usuario" in html
m = re.search(r'<label for="nom_nouveau">([^<]*)</label>', html)
print("label creation:", repr(m.group(1) if m else "MISSING"))
print("OK")
