import re
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def login():
    body = urllib.parse.urlencode(
        {"email": "admin@admin.com", "mot_de_passe": "admin123"}
    ).encode()
    opener.open(urllib.request.Request(f"{BASE}/login", data=body, method="POST"))

def get_users():
    login()
    return opener.open(f"{BASE}/admin/users").read().decode()

def post_modify(user_id: int, data: dict):
    login()
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"{BASE}/admin/users/{user_id}/modifier",
        data=body,
        method="POST",
    )
    try:
        resp = opener.open(req)
        print("POST", user_id, "->", resp.status, resp.geturl())
    except urllib.error.HTTPError as exc:
        print("POST", user_id, "-> HTTP", exc.code)
        print(exc.read().decode()[:2000])

html = get_users()
match = re.search(r'data-id="(\d+)".*?data-email="([^"]+)".*?data-prenom="([^"]*)".*?data-nom-famille="([^"]*)".*?data-role="([^"]+)"', html, re.S)
if match:
    uid, email, prenom, apellido, role = match.groups()
    print("FOUND USER", uid, email, prenom, apellido, role)
    post_modify(
        int(uid),
        {
            "email": email,
            "prenom": prenom or "Flora",
            "nom_famille": apellido or "Test",
            "mot_de_passe": "",
            "role": role if role in ("admin", "user") else "user",
        },
    )
else:
    print("NO USER BUTTON FOUND")
    print(html[html.find("btn-modifier-compte"):html.find("btn-modifier-compte")+500])
