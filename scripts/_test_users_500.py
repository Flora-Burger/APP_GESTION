import sys
import traceback

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)
client.post("/login", data={"email": "admin@admin.com", "mot_de_passe": "admin123"})
r = client.get("/admin/users")
print("status", r.status_code)
if r.status_code >= 400:
    print(r.text[:4000])

try:
    client2 = TestClient(app, raise_server_exceptions=True)
    client2.post("/login", data={"email": "admin@admin.com", "mot_de_passe": "admin123"})
    client2.get("/admin/users")
except Exception:
    traceback.print_exc()
