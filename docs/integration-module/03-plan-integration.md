# 03 — Plan d'integration (phases 0 a 6)

## Phase 0 — Preparation

- [ ] Cloner ou copier APP_GESTION dans le monorepo hote (ex. `packages/flora/` ou `modules/app_gestion/`)
- [ ] Completer `02-analyse-application-hote.md`
- [ ] Choisir le scenario dans `05-scenarios-et-decisions.md`
- [ ] Creer branche Git dediee

## Phase 1 — Dependances et configuration

- [ ] Fusionner `requirements.txt` / `pyproject.toml` (versions compatibles)
- [ ] Ajouter variables d'env au `.env.example` hote :

```env
# FLORA / APP_GESTION
NOM_ENTREPRISE=Mon Entreprise
LOGO_URL=/static/img/logo.png
DATABASE_URL=sqlite:///./data/flora.db
JWT_SECRET=changez-moi-en-production
JWT_EXPIRATION_MINUTES=480
COOKIE_AUTH_NOM=flora_token
COOKIE_SECURE=false
BLOB_READ_WRITE_TOKEN=
```

- [ ] Verifier `RACINE_PROJET` dans `backend/app/core/config.py` :
  - Aujourd'hui : `Path(__file__).resolve().parents[3]` → racine APP_GESTION
  - Si le code est deplace : ajuster `parents[N]` ou passer la racine en parametre / variable d'env

## Phase 2 — Base de donnees

### Option A — Meme base que l'hote

- [ ] Pointer `DATABASE_URL` vers la base hote
- [ ] Executer migrations FLORA :

```bash
# Depuis la racine APP_GESTION (ou avec alembic.ini adapte)
alembic upgrade head
```

- [ ] Verifier dans `backend/alembic/env.py` que tous les modeles sont importes

### Option B — Base dediee FLORA

- [ ] Configurer une seconde `DATABASE_URL` (ex. `FLORA_DATABASE_URL`)
- [ ] **Refactor necessaire** : `database.py` actuel utilise un engine global unique — extraire un second engine ou isoler dans un module

### Fusion Alembic (hote deja sous Alembic)

- [ ] Copier les revisions FLORA dans l'arborescence Alembic hote
- [ ] Rebasculer les `down_revision` pour s'enchainer apres la tete hote
- [ ] Tester `alembic upgrade head` sur une base vide puis sur staging

## Phase 3 — Factory d'enregistrement du module

Creer `backend/app/integration.py` (ou equivalent dans le hote) :

```python
"""Enregistrement du module FLORA dans une application FastAPI hote."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.core.auth_middleware import AuthMiddleware
from backend.app.core.config import RACINE_PROJET
# ... imports routers ...

def monter_flora(
    app: FastAPI,
    *,
    prefix: str = "",
    activer_auth_middleware: bool = True,
    activer_static: bool = True,
    activer_seed_admin: bool = True,
) -> None:
    """Monte routes, middleware et fichiers statiques FLORA."""
    if activer_auth_middleware:
        app.add_middleware(AuthMiddleware)  # ATTENTION : middleware global

    if activer_static:
        dossier = RACINE_PROJET / "static"
        if dossier.is_dir():
            app.mount(f"{prefix}/static", StaticFiles(directory=str(dossier)), name="flora_static")

    app.include_router(router_auth, prefix=prefix)
    app.include_router(router_accueil, prefix=prefix)
    # ... autres routers avec le meme prefix ...
    app.include_router(router_api_vehicules, prefix=f"{prefix}/api/v1")
    # ...
```

**Points a implementer reellement** (le snippet est un guide) :

1. Gestion du `lifespan` (seed admin) — fusionner avec le lifespan hote si existant
2. `exception_handler` pour validation formulaire admin users
3. Si `prefix != ""` : mettre a jour `AuthMiddleware.CHEMINS_PUBLICS` et redirections `/login`
4. Si `prefix != ""` : mettre a jour liens dans templates (`base.html`, formulaires, HTMX)

### Integration dans le main hote

```python
from backend.app.integration import monter_flora

app = FastAPI(lifespan=lifespan_hote)
# ... routes hote ...
monter_flora(app, prefix="/flora")
```

## Phase 4 — Authentification

### Si scenario A (auth FLORA native)

- [ ] Monter `AuthMiddleware` — verifier qu'il ne bloque pas les routes publiques hote
- [ ] Etendre `CHEMINS_PUBLICS` si besoin :

```python
CHEMINS_PUBLICS = (
    "/login",
    f"{prefix}/login",  # si prefixe
    "/static",
    f"{prefix}/static",
    # routes publiques hote...
)
```

- [ ] Changer `COOKIE_AUTH_NOM` si conflit avec l'hote

### Si scenario B (auth hote)

- [ ] Ne pas monter `AuthMiddleware` FLORA
- [ ] Creer middleware/adaptateur hote qui remplit `request.state.utilisateur`
- [ ] Mapper les roles hote → `admin` | `user`
- [ ] Desactiver routes `/login`, `/logout`, `/admin/users` FLORA ou les rediriger
- [ ] Desactiver `initialiser_admin_par_defaut`

## Phase 5 — Templates, static, navigation

- [ ] Ajuster `LOGO_URL` et liens CSS si prefixe :

```html
<!-- base.html — exemple avec prefixe /flora -->
<link rel="stylesheet" href="/flora/static/css/style.css?v=...">
```

- [ ] Option : injecter `prefixe_url` dans `contexte_template()` pour eviter les chemins en dur
- [ ] Ajouter lien vers FLORA dans la navigation de l'hote (menu, sidebar)
- [ ] Decider du sort de la page `/` FLORA (dashboard) vs accueil hote

## Phase 6 — Fichiers et deploiement

- [ ] Configurer stockage uploads (local ou `BLOB_READ_WRITE_TOKEN`)
- [ ] Sur Vercel : `VERCEL=1`, PostgreSQL obligatoire, `vercel.json` de reference
- [ ] Documenter commandes de demarrage post-integration
- [ ] Executer `06-verification.md`

## Fichiers susceptibles d'etre modifies

| Fichier | Modification typique |
|---------|---------------------|
| `backend/app/main.py` (hote) | Appel `monter_flora()` |
| `backend/app/integration.py` (nouveau) | Factory |
| `backend/app/core/config.py` | `RACINE_PROJET`, nouvelles env vars |
| `backend/app/core/auth_middleware.py` | Chemins publics, prefixe |
| `backend/app/core/dependances.py` | `contexte_template` + prefixe URL |
| `backend/app/templates/base.html` | Liens static et navigation |
| `alembic.ini` | Chemin si structure change |
| `.env` / `.env.example` | Variables FLORA |

## Anti-patterns a eviter

- Monter FLORA a la racine sans verifier les collisions avec l'hote
- Deux `AuthMiddleware` en conflit (hote + FLORA) sans ordre ni chemins exclusifs
- Oublier de migrer la DB avant les tests
- Laisser `JWT_SECRET` par defaut en production
- Commiter des uploads utilisateurs (`static/uploads/`) dans le repo hote sans politique claire
