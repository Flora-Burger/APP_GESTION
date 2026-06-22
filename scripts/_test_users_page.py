import sys
import traceback

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from datetime import datetime

from starlette.requests import Request

from backend.app.core.dependances import contexte_template, templates
from backend.app.modules.auth.schemas import RoleUtilisateur, UtilisateurResponse

scope = {"type": "http", "method": "GET", "path": "/admin/users", "headers": [], "query_string": b""}
request = Request(scope)

admin = UtilisateurResponse(
    id=1,
    email="admin@admin.com",
    nom="Admin Principal",
    role=RoleUtilisateur.ADMIN,
    est_actif=True,
    cree_le=datetime.now(),
)
user = UtilisateurResponse(
    id=2,
    email="user@test.com",
    nom="Maria Garcia",
    role=RoleUtilisateur.USER,
    est_actif=True,
    cree_le=datetime.now(),
)

try:
    ctx = contexte_template(
        request,
        utilisateurs=[admin, user],
        message=None,
        erreur=None,
        modifier_id=None,
    )
    ctx["utilisateur_courant"] = admin
    html = templates.env.get_template("admin/users.html").render(ctx)
    print("RENDER OK", len(html))
except Exception:
    traceback.print_exc()
