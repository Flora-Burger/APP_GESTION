import re
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

body = urllib.parse.urlencode({"email": "admin@admin.com", "mot_de_passe": "admin123"}).encode()
opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))

# toggle should use same admin from middleware
try:
    resp = opener.open(urllib.request.Request(f"{BASE}/admin/users/3/toggle", data=b"", method="POST"))
    print("toggle", resp.status, resp.geturl())
except urllib.error.HTTPError as exc:
    print("toggle HTTP", exc.code, exc.read()[:500])

# modify with explicit good role
data = urllib.parse.urlencode(
    {
        "email": "user@test.com",
        "prenom": "Test",
        "nom_famille": "User",
        "mot_de_passe": "",
        "role": "user",
    }
).encode()
try:
    resp = opener.open(urllib.request.Request(f"{BASE}/admin/users/3/modifier", data=data, method="POST"))
    print("modify", resp.status, resp.geturl())
except urllib.error.HTTPError as exc:
    print("modify HTTP", exc.code)
    print(exc.read().decode()[:1000])
