"""Test via FastAPI TestClient."""
import re
import sys

sys.path.insert(0, "e:/FLORA/APP_GESTION")

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# login
r = client.post("/login", data={"email": "admin@admin.com", "mot_de_passe": "admin123"})
print("login:", r.status_code)

page = client.get("/admin/users")
html = page.text

for field in ("email", "nom", "mot_de_passe", "role"):
    m = re.search(rf'<label for="{field}">([^<]*)</label>', html)
    print(f"label {field}:", repr(m.group(1) if m else "MISSING"))

from backend.app.traductions.es import TRADUCTIONS
print("TRADUCTIONS nom:", repr(TRADUCTIONS.get("nom")))
