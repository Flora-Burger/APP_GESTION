import re
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://localhost:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

body = urllib.parse.urlencode({"email": "admin@admin.com", "mot_de_passe": "admin123"}).encode()
opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))

try:
    resp = opener.open(f"{BASE}/admin/users")
    html = resp.read().decode()
    print("STATUS", resp.status)
    print("HAS TABLE", "tableau-historique" in html)
    print("HAS ERROR", "Internal Server Error" in html)
    if "Traceback" in html or "Error" in html[:500]:
        print(html[:2000])
except urllib.error.HTTPError as exc:
    print("HTTP", exc.code)
    print(exc.read().decode()[:3000])
