import re
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://localhost:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

body = urllib.parse.urlencode({"email": "admin@admin.com", "mot_de_passe": "admin123"}).encode()
opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))
html = opener.open(f"{BASE}/admin/users").read().decode()

rows = re.findall(r"<tbody>(.*?)</tbody>", html, re.S)
if rows:
    trs = re.findall(r"<tr>", rows[0])
    print("ROWS", len(trs))
    print(rows[0][:1500])
else:
    print("NO TBODY")

print("lignes_utilisateurs" in html, "utilisateurs loop" in html)

import sys
sys.path.insert(0, "e:/FLORA/APP_GESTION")
from backend.app.core.database import SessionLocal
from backend.app.modules.auth.service import AuthService

session = SessionLocal()
try:
    users = AuthService(session).lister_utilisateurs()
    print("DB USERS", len(users))
    for u in users:
        print("-", u.id, u.email, u.nom, u.role)
finally:
    session.close()
