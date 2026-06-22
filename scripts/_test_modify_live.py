import urllib.error
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
        "email": "anna@anna.com",
        "nom": "Anna",
        "mot_de_passe": "",
        "role": "user",
    }
).encode()

try:
    resp = opener.open(
        urllib.request.Request(f"{BASE}/admin/users/4/modifier", data=data, method="POST")
    )
    print("OK", resp.status, resp.geturl())
except urllib.error.HTTPError as exc:
    print("HTTP", exc.code)
    print(exc.read().decode()[:3000])
