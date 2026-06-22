# FLORA - Gestion des ressources

Application modulaire de gestion des ressources materielles de l'entreprise.

- **Code** : Python (francais)
- **Interface** : Espagnol
- **Stack** : FastAPI, SQLAlchemy, Jinja2, HTMX

## Prerequis

- Python 3.11 ou superieur installe et accessible dans le PATH

## Installation

```powershell
cd e:\FLORA\APP_GESTION

# Creer l'environnement virtuel VFLORA
python -m venv VFLORA

# Activer l'environnement
.\VFLORA\Scripts\Activate.ps1

# Installer les dependances
pip install -r requirements.txt

# Copier la configuration
copy .env.example .env

# Appliquer les migrations
alembic upgrade head

# Inserer des donnees d'exemple
python scripts/seed_donnees.py
```

## Lancement

### Windows (doble clic)

Ejecute [`iniciar.bat`](iniciar.bat) en la raiz del proyecto.

**Cuenta admin por defecto:** `001` / `admin123`

### Manual (PowerShell)

```powershell
.\VFLORA\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

- **Interface web** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs

## Modules disponibles

| Module | Etat | Route |
|--------|------|-------|
| Vehiculos | Actif | `/vehicules` |
| Ordenadores | Proximamente | - |
| Impresoras | Proximamente | - |

## Documentation

- [Architecture](docs/architecture.md)
- [Autenticacion](docs/authentification.md)
- [Module Vehicules](docs/module-vehicules.md)
- [Module Imprimantes](docs/module-imprimantes.md)

## Structure

```
APP_GESTION/
├── VFLORA/           # Environnement virtuel
├── backend/          # Application Python
├── static/           # Fichiers statiques (CSS, images)
├── scripts/          # Scripts utilitaires
└── docs/             # Documentation
```
