"""Fetch admin users page HTML after login."""
import re
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://localhost:8001"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def post_form(url: str, data: dict) -> str:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with opener.open(req) as resp:
        return resp.read().decode()


def get(url: str) -> str:
    with opener.open(url) as resp:
        return resp.read().decode()


post_form(f"{BASE}/login", {"email": "admin@admin.com", "mot_de_passe": "admin123"})
html = get(f"{BASE}/admin/users")

marker = 'for="nom_utilisateur"'
idx = html.find(marker)
if idx < 0:
    print("NO nom_utilisateur label in live page")
else:
    print("LIVE SNIPPET:", repr(html[idx - 20 : idx + 120]))

for field in ("email", "nom_utilisateur", "mot_de_passe", "role"):
    m = re.search(rf'<label for="{field}">([^<]*)</label>', html)
    print(f"label {field}:", repr(m.group(1) if m else "MISSING"))

ths = re.findall(r"<th>([^<]*)</th>", html)
print("table headers:", ths)
