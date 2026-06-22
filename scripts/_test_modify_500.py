import sys
import traceback

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from starlette.datastructures import FormData
from starlette.requests import Request

from backend.app.core.database import SessionLocal
from backend.app.modules.auth.router_admin import modifier_utilisateur
from backend.app.modules.auth.service import AuthService


async def main():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/admin/users/2/modifier",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("127.0.0.1", 8000),
    }
    request = Request(scope)
    session = SessionLocal()
    try:
        admin = AuthService(session).lister_utilisateurs()[0]
        request.state.utilisateur = admin

        for role in ("user", "RoleUtilisateur.USER", "admin"):
            print("--- role =", role)
            try:
                resp = modifier_utilisateur(
                    request,
                    2,
                    email="brg.flora@gmail.com",
                    prenom="Flora",
                    nom_famille="Garcia",
                    mot_de_passe="",
                    role=role,
                    session=session,
                )
                print("OK", resp.status_code, resp.headers.get("location"))
            except Exception:
                traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
