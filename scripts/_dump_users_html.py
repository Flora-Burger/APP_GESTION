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

m = re.search(r"<table class=\"tableau-historique\">(.*?)</table>", html, re.S)
if m:
    print(m.group(1))
else:
    print("NO TABLE")

print("---")
print("for ligne in lignes_utilisateurs" in html)
print("for u in utilisateurs" in html)
