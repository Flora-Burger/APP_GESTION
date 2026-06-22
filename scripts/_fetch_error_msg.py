"""Check if nom_obligatoire translation works on live server."""
import re
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://localhost:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post_form(url: str, data: dict) -> None:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    opener.open(req)


def get(url: str) -> str:
    with opener.open(url) as resp:
        return resp.read().decode()


post_form(f"{BASE}/login", {"email": "admin@admin.com", "mot_de_passe": "admin123"})
html = get(f"{BASE}/admin/users?erreur=nom_obligatoire")

m = re.search(r'message-erreur">([^<]+)</div>', html)
print("error message:", repr(m.group(1) if m else "MISSING"))

html2 = get(f"{BASE}/admin/users")
if "Nombre" in html2:
    print("Nombre found in page")
else:
    print("Nombre NOT in page")
