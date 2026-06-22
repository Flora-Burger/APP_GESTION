import asyncio
import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from starlette.requests import Request

from backend.app.core.database import SessionLocal
from backend.app.modules.auth.router_admin import page_utilisateurs


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
        from backend.app.modules.auth.service import AuthService

        utilisateurs = AuthService(session).lister_utilisateurs()
        request.state.utilisateur = utilisateurs[0]
        response = page_utilisateurs(request, session)
        html = response.body.decode()
        header = re.search(r"<th>Identificador</th>\s*<th>(.*?)</th>", html, re.S)
        role = re.search(r'data-role="([^"]+)"', html)
        rows = len(re.findall(r"<tbody>.*?<tr>", html, re.S))
        print("header_nom", repr(header.group(1).strip() if header else None))
        print("data_role", role.group(1) if role else None)
        print("has_rows", "001" in html)
    finally:
        session.close()


asyncio.run(main())
