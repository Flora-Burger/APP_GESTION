"""Verifier le rendu du libelle nom sur la page admin users."""
import re
import sys
import urllib.parse
import urllib.request
import http.cookiejar

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from backend.app.core.dependances import templates
from backend.app.traductions.es import TRADUCTIONS

html_local = templates.env.get_template("admin/users.html").render(
    request=None,
    t=TRADUCTIONS,
    nom_entreprise="X",
    logo_url="",
    utilisateur_courant=None,
    nom_utilisateur_courant="",
    est_admin=True,
    utilisateurs=[],
    message=None,
    erreur=None,
    roles=None,
)

m = re.search(r'<label for="nom_utilisateur">([^<]*)</label>', html_local)
print("LOCAL label:", repr(m.group(1) if m else "MISSING"))
print("LOCAL has key:", "nom_utilisateur" in TRADUCTIONS)

BASE = "http://localhost:8000"
try:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    body = urllib.parse.urlencode(
        {"email": "admin@admin.com", "mot_de_passe": "admin123"}
    ).encode()
    opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))
    html_live = opener.open(f"{BASE}/admin/users").read().decode()
    m2 = re.search(r'<label for="nom_utilisateur">([^<]*)</label>', html_live)
    print("LIVE label:", repr(m2.group(1) if m2 else "MISSING"))
    idx = html_live.find("nom_utilisateur")
    if idx >= 0:
        print("LIVE snippet:", repr(html_live[idx - 40 : idx + 120]))
except Exception as exc:
    print("LIVE error:", exc)
