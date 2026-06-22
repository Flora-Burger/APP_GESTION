import asyncio
import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from starlette.requests import Request

from backend.app.core.database import SessionLocal
from backend.app.modules.auth.router_admin import page_utilisateurs
from backend.app.modules.auth.service import AuthService


async def main():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/admin/users",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("127.0.0.1", 8000),
    }
    request = Request(scope)
    session = SessionLocal()
    try:
        utilisateurs = AuthService(session).lister_utilisateurs()
        request.state.utilisateur = utilisateurs[0]
        html = page_utilisateurs(request, session).body.decode()
        rows = re.findall(r"<tbody>(.*?)</tbody>", html, re.S)[0]
        print(rows)
    finally:
        session.close()


asyncio.run(main())
