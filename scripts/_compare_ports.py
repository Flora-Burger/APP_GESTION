import re
import urllib.parse
import urllib.request
import http.cookiejar

for port in (8000, 8001):
    base = f"http://localhost:{port}"
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        body = urllib.parse.urlencode(
            {"email": "001", "mot_de_passe": "admin123"}
        ).encode()
        opener.open(urllib.request.Request(f"{base}/login", data=body, method="POST"))
        html = opener.open(f"{base}/admin/users").read().decode()
        rows = re.findall(r"<tbody>(.*?)</tbody>", html, re.S)
        tr_count = len(re.findall(r"<tr>", rows[0])) if rows else 0
        role_match = re.search(r'data-role="([^"]+)"', html)
        header_match = re.search(r"<th>Identificador</th>\s*<th>(.*?)</th>", html, re.S)
        print(
            port,
            "rows=",
            tr_count,
            "header_nom=",
            repr(header_match.group(1).strip() if header_match else None),
            "data_role=",
            role_match.group(1) if role_match else None,
        )
    except Exception as exc:
        print(port, "error", exc)
