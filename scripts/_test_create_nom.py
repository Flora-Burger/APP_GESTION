import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

login = urllib.parse.urlencode(
    {"email": "admin@admin.com", "mot_de_passe": "admin123"}
).encode()
opener.open(urllib.request.Request(f"{BASE}/login", data=login, method="POST"))

data = urllib.parse.urlencode(
    {
        "email": "test_nom@test.com",
        "nom": "NombreTest",
        "mot_de_passe": "test123",
        "role": "user",
    }
).encode()
resp = opener.open(urllib.request.Request(f"{BASE}/admin/users", data=data, method="POST"))
print("create redirect", resp.geturl())

import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.repository import UtilisateurRepository

session = SessionLocal()
user = UtilisateurRepository(session).obtenir_par_email("test_nom@test.com")
print("saved nom", repr(user.nom if user else None))
if user:
    UtilisateurRepository(session).supprimer(user)
    session.commit()
session.close()
