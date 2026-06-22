import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

body = urllib.parse.urlencode({"email": "admin@admin.com", "mot_de_passe": "admin123"}).encode()
opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))

for url in [
    f"{BASE}/admin/users?modifier_id=2",
    f"{BASE}/admin/users?erreur=erreur_modification&modifier_id=2",
]:
    try:
        resp = opener.open(url)
        html = resp.read().decode()
        print(url, "->", resp.status, "ERR" if "Internal Server Error" in html else "OK")
    except Exception as exc:
        print(url, "->", exc)
