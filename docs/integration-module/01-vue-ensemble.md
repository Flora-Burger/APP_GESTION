# 01 — Vue d'ensemble du module FLORA

## Identite du projet

| Attribut | Valeur |
|----------|--------|
| Nom interne | FLORA / APP_GESTION |
| Role | Gestion de parc materiel d'entreprise |
| Modules metier | Vehicules, imprimantes, ordinateurs |
| Langue du code | Francais (noms, commentaires) |
| Langue de l'interface | Espagnol (`backend/app/traductions/es.py`) |
| Type d'integration | Application FastAPI **autonome** a monter dans un hote — pas un package pip |

## Stack technique

- **FastAPI** + Uvicorn
- **SQLAlchemy 2.x** + **Alembic** (15 migrations, 001 → 015)
- **SQLite** en dev (`data/flora.db`), **PostgreSQL** en prod / Vercel
- **Jinja2** + **HTMX 2.x** (CDN unpkg)
- **Auth** : JWT dans cookie HTTP-only + bcrypt, roles `admin` | `user`
- **Fichiers** : stockage local (`static/uploads/`) ou **Vercel Blob** en production

## Arborescence a integrer

```
APP_GESTION/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Reference actuelle — a transformer en factory
│   │   ├── core/                   # Config, DB, auth, templates, stockage
│   │   ├── modules/
│   │   │   ├── auth/               # Login, users admin, contacts
│   │   │   ├── accueil/            # Dashboard /
│   │   │   ├── vehicules/          # + configuration globale seguro/talleres
│   │   │   ├── imprimantes/
│   │   │   ├── ordinateurs/
│   │   │   └── base/               # registre_modules.py
│   │   ├── templates/              # Tous les HTML Jinja2
│   │   └── traductions/es.py
│   └── alembic/                    # Migrations
├── static/
│   ├── css/style.css, mobile.css
│   ├── img/
│   └── uploads/                    # Dev local ; prod = Blob si configure
├── alembic.ini
├── requirements.txt
└── docs/
```

## Pattern modulaire interne

Chaque ressource suit la meme structure :

```
modules/<nom>/
├── modeles.py          # Tables SQLAlchemy
├── schemas.py          # Pydantic
├── repository.py       # Acces donnees
├── service.py          # Logique metier
├── router_web.py       # Pages HTML
├── router_admin.py     # Admin HTML (si applicable)
└── router_api.py       # REST /api/v1/...
```

Les routers declarent des **chemins absolus** dans les decorateurs (`@router.get("/vehicules")`), pas de `prefix` sur le `APIRouter` (sauf API avec `/api/v1` dans `main.py`).

## Enregistrement actuel dans main.py

Ordre de montage (reference `backend/app/main.py`) :

1. `AuthMiddleware` (global)
2. Mount `/static`
3. `router_auth` — `/login`, `/logout`, `/contacts`
4. `router_accueil` — `/`, `/partials/recherche`
5. Routers web vehicules, imprimantes, ordinateurs
6. Routers admin auth + admin par module
7. Routers API avec `prefix="/api/v1"`

## Lifespan au demarrage

Au startup, FLORA cree un admin par defaut si absent :

- Identifiant : `001`
- Mot de passe : `admin123`

Via `AuthService(session).initialiser_admin_par_defaut()`.

**A desactiver** si l'hote fournit deja la gestion des utilisateurs.

## Contrat template (contexte Jinja2)

Toutes les pages utilisent `contexte_template(request, **kwargs)` (`backend/app/core/dependances.py`) qui injecte :

| Cle | Description |
|-----|-------------|
| `t` | Dictionnaire de traductions espagnoles |
| `nom_entreprise`, `logo_url` | Branding |
| `utilisateur_courant` | Objet `Utilisateur` SQLAlchemy |
| `nom_utilisateur_courant` | Nom affiche |
| `est_admin` | Bool |
| `modules_navigation` | Liste depuis `registre_modules.py` |

**Pre-requis** : `request.state.utilisateur` doit etre defini par le middleware (ou adaptateur auth hote).

## Contrat auth

| Role | Acces |
|------|-------|
| `admin` | Tout : dashboard, tous les vehicules, pages `/admin/*` |
| `user` | Vehicule assigne uniquement ; mobile redirige `/` → `/vehicules` ; pas d'admin |

Verification admin web : `verifier_admin_web(request)` dans `core/admin_web.py`.

Verification API : `Depends(obtenir_utilisateur_connecte)` et `exiger_admin`.

## Ce que le module apporte a l'hote

- UI web complete (listes, historiques, formulaires HTMX, admin)
- API REST versionnee (`/api/v1/...`)
- Gestion utilisateurs FLORA (table `utilisateurs` dediee)
- Upload photos / factures
- Configuration globale flotte (seguro, talleres de referencia)

## Ce que le module n'apporte pas

- Pas de prefixe URL configurable sans modification
- Pas d'isolation schema PostgreSQL native
- Pas d'i18n multi-langue (espagnol uniquement)
- Pas de tests d'integration fournis pour le montage dans un hote
