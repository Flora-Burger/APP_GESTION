# 04 — Reference technique

## Variables d'environnement

| Variable | Defaut FLORA | Description |
|----------|--------------|-------------|
| `NOM_ENTREPRISE` | `FLORA` | Titre dans l'en-tete |
| `LOGO_URL` | `/static/img/logo.png` | Logo |
| `DATABASE_URL` | `sqlite:///.../data/flora.db` | Connexion SQLAlchemy |
| `DEBUG` | `true` | Echo SQL |
| `JWT_SECRET` | *(dev insecure)* | **Obligatoire en prod** |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRATION_MINUTES` | `480` | |
| `COOKIE_AUTH_NOM` | `flora_token` | Nom du cookie JWT |
| `COOKIE_SECURE` | `false` | `true` force sur Vercel |
| `BLOB_READ_WRITE_TOKEN` | — | Vercel Blob (uploads prod) |

**Lues directement (hors Parametres)** :

| Variable | Usage |
|----------|-------|
| `VERCEL` | `1` → mode Vercel, PG obligatoire |
| `VERCEL_OIDC_TOKEN` | Auth Blob sur Vercel |
| `BLOB_STORE_ID` | ID store Blob |

Fichier `.env` charge depuis `RACINE_PROJET / ".env"`.

---

## Tables SQL (sans prefixe)

| Table | Module |
|-------|--------|
| `utilisateurs` | auth |
| `vehicules` | vehicules |
| `vehicule_journaux` | vehicules |
| `vehicule_immobilisations` | vehicules |
| `vehicules_configuration` | vehicules (seguro/talleres globaux) |
| `imprimantes` | imprimantes |
| `imprimante_evenements` | imprimantes |
| `ordinateurs` | ordinateurs |
| `ordinateur_evenements` | ordinateurs |

**Pas de FK** vers `utilisateurs` depuis les ressources : assignation vehicule par **nom affiche** (string).

---

## Routes web

### Auth

| Methode | Chemin | Description |
|---------|--------|-------------|
| GET/POST | `/login` | Connexion |
| POST | `/logout` | Deconnexion |
| GET | `/contacts` | Annuaire employes |

### Accueil

| Methode | Chemin | Description |
|---------|--------|-------------|
| GET | `/` | Dashboard |
| GET | `/partials/recherche` | Recherche globale HTMX |

### Vehicules (extrait)

| Methode | Chemin | Description |
|---------|--------|-------------|
| GET | `/vehicules` | Liste |
| GET | `/vehicules/{id}/historique` | Historique |
| POST | `/vehicules/{id}/journal` | Donnees du jour |
| POST | `/vehicules/{id}/garage` | Envoi au taller |
| GET | `/admin/vehicules` | Admin liste |
| GET/POST | `/admin/vehicules/configuracion` | Seguro y talleres |

### Imprimantes / Ordinateurs

| Prefixe | Description |
|---------|-------------|
| `/imprimantes`, `/admin/imprimantes` | Parc imprimantes |
| `/ordinateurs`, `/admin/ordinateurs` | Parc ordinateurs |

### Admin utilisateurs

| Methode | Chemin |
|---------|--------|
| GET/POST | `/admin/users` |
| POST | `/admin/users/{id}/modifier` |
| POST | `/admin/users/{id}/toggle` |
| POST | `/admin/users/{id}/supprimer` |

---

## Routes API REST

Prefixe commun : `/api/v1`

| Chemin | Module |
|--------|--------|
| `/api/v1/vehicules` | CRUD vehicules |
| `/api/v1/imprimantes` | CRUD imprimantes |
| `/api/v1/ordinateurs` | CRUD ordinateurs |
| `/api/v1/recherche` | Recherche globale |

Toutes protegees par `Depends(obtenir_utilisateur_connecte)` + middleware.

---

## Fichiers core — roles

| Fichier | Role |
|---------|------|
| `core/config.py` | `Parametres`, `RACINE_PROJET`, Vercel |
| `core/database.py` | `engine`, `SessionLocal`, `Base`, `obtenir_session` |
| `core/auth_middleware.py` | Protection globale routes |
| `core/auth_dependances.py` | DI utilisateur API |
| `core/admin_web.py` | `verifier_admin_web()` |
| `core/securite.py` | bcrypt + JWT |
| `core/dependances.py` | Jinja2 + `contexte_template` |
| `core/stockage_fichiers.py` | Local / Vercel Blob |

---

## Modules — routers exportes

| Module | router_web | router_admin | router_api |
|--------|------------|--------------|------------|
| auth | `router_web` | `router_admin` | — |
| accueil | `router_web` | — | — |
| vehicules | `router_web` | `router_admin` | `router_api` |
| imprimantes | `router_web` | `router_admin` | `router_api` |
| ordinateurs | `router_web` | `router_admin` | `router_api` |

Import pattern dans `main.py` :

```python
from backend.app.modules.vehicules.router_web import router as router_web_vehicules
```

---

## Migrations Alembic (ordre)

| Rev | Fichier |
|-----|---------|
| 001 | `001_creation_tables_vehicules.py` |
| 002 | `002_champs_vehicules_itv_journal.py` |
| 003 | `003_kilometrage_de_base.py` |
| 004 | `004_table_utilisateurs.py` |
| 005 | `005_suppression_itv_valide.py` |
| 006 | `006_tables_imprimantes.py` |
| 007 | `007_tables_ordinateurs.py` |
| 008 | `008_table_vehicule_immobilisations.py` |
| 009 | `009_journal_actif_multi_utilisateur.py` |
| 010 | `010_suppression_kilometrage_vehicules.py` |
| 011 | `011_kilometrage_vehicules.py` |
| 012 | `012_identifiant_3_chiffres.py` |
| 013 | `013_refonte_admin_user.py` |
| 014 | `014_configuration_vehicules_globale.py` |
| 015 | `015_correo_utilisateur.py` |

Config : `alembic.ini` → `script_location = backend/alembic`

---

## Templates principaux

| Template | Role |
|----------|------|
| `base.html` | Layout, nav, CSS, HTMX |
| `auth/login.html` | Page connexion |
| `contacts/liste.html` | Annuaire |
| `vehicules/liste.html` | Liste vehicules |
| `vehicules/partials/infos_flotte.html` | Seguro + talleres |
| `admin/*.html` | Interfaces admin |
| `partials/menu_lateral_mobile.html` | Menu mobile |

---

## Static

| Chemin | Contenu |
|--------|---------|
| `/static/css/style.css` | Styles bureau |
| `/static/css/mobile.css` | Styles mobile (≤768px) |
| `/static/img/logo.png` | Logo par defaut |
| `/static/uploads/vehicules/` | Photos vehicules (dev) |
| `/static/uploads/imprimantes/factures/` | Factures |
| `/static/uploads/ordinateurs/` | Photos + factures |

---

## Registre navigation modules

`backend/app/modules/base/registre_modules.py` — modifier `MODULES_RESSOURCES` pour activer/desactiver des modules dans le menu et le dashboard.

---

## Dependances Python (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.36
alembic>=1.14.0
pydantic-settings>=2.6.0
jinja2>=3.1.4
python-multipart>=0.0.12
psycopg[binary]>=3.2.0
httpx>=0.28.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.2.0
email-validator>=2.2.0
```

Python recommande : **≥ 3.12**

---

## Imports Python

Tous les imports internes utilisent :

```python
from backend.app.core.database import obtenir_session
from backend.app.modules.vehicules.service import VehiculeService
```

Le repertoire parent de `backend/` doit etre sur `PYTHONPATH`, ou refactoriser vers le package de l'hote.
