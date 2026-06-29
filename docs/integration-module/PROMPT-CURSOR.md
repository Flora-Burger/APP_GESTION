# Prompt Cursor — Integrer FLORA comme module

> Copiez ce fichier dans le chat Cursor du **projet hote**, apres avoir rempli les sections `[A REMPLIR]`.
> Joignez aussi le dossier `docs/integration-module/` du depot APP_GESTION (ou donnez le chemin vers le code source FLORA).

---

## Mission

Tu dois integrer le projet **APP_GESTION (FLORA)** — gestion de ressources materielles (vehicules, imprimantes, ordinateurs) — comme **module** dans l'application FastAPI existante decrite ci-dessous.

FLORA est une app FastAPI + Jinja2 + HTMX avec auth JWT (cookie), SQLAlchemy et Alembic. Il n'existe pas encore de fonction `monter_flora()` : tu dois la creer ou integrer manuellement en suivant la documentation du dossier `docs/integration-module/`.

**Lis d'abord** (dans le depot FLORA) :
- `docs/integration-module/01-vue-ensemble.md`
- `docs/integration-module/02-analyse-application-hote.md`
- `docs/integration-module/03-plan-integration.md`
- `docs/integration-module/04-reference-technique.md`
- `docs/integration-module/05-scenarios-et-decisions.md`

---

## Application hote — contexte

```
[A REMPLIR — ex.]
- Chemin du projet hote : /chemin/vers/mon-app
- Chemin du code FLORA : /chemin/vers/APP_GESTION (ou sous-dossier copie)
- Framework : FastAPI x.x
- Base de donnees : PostgreSQL / SQLite / autre
- Auth existante : oui/non — si oui, decrire (JWT, session, OAuth, table users, etc.)
- Prefixe URL souhaite pour FLORA : ex. /flora ou / (racine)
- Scenario choisi : A / B / C / D (voir 05-scenarios-et-decisions.md)
```

---

## Contraintes obligatoires

1. **Ne pas casser l'application hote** : les routes et fonctionnalites existantes doivent continuer a fonctionner.
2. **Eviter les collisions de routes** : FLORA utilise `/`, `/login`, `/vehicules`, `/admin/*`, `/api/v1/*`, `/static/*` par defaut. Adapter avec un prefixe si necessaire.
3. **Base de donnees** : executer les migrations Alembic FLORA (`backend/alembic/`, revisions 001 a 015) sur la base choisie, ou documenter pourquoi une base separee est utilisee.
4. **Imports** : le code FLORA utilise le prefixe `backend.app.*`. Soit le PYTHONPATH inclut la racine APP_GESTION, soit refactoriser les imports vers le package de l'hote (ex. `mon_app.flora.*`).
5. **Auth** :
   - Scenario A (auth FLORA) : monter `AuthMiddleware` en veillant a ne pas bloquer les routes publiques de l'hote.
   - Scenario B (auth hote) : adapter pour remplir `request.state.utilisateur` avec la forme attendue (id, email, nom, role, est_actif).
6. **Templates et static** : les templates FLORA referencent `/static/css/...`. Si prefixe URL, mettre a jour `base.html`, `login.html` et le mount StaticFiles.
7. **Variables d'environnement** : fusionner avec le `.env` de l'hote (`DATABASE_URL`, `JWT_SECRET`, `COOKIE_AUTH_NOM`, etc.) — eviter les conflits de noms de cookie.
8. **Code en francais** : conserver noms de fonctions, commentaires et structure existants de FLORA ; interface utilisateur en espagnol (`traductions/es.py`).
9. **Minimal scope** : ne refactoriser que ce qui est necessaire a l'integration ; pas de refonte esthetique ou fonctionnelle non demandee.

---

## Livrables attendus

1. **Fichier d'enregistrement du module** — ex. `monter_flora(app: FastAPI, prefix: str = "/flora")` dans le projet hote ou dans FLORA (`backend/app/integration.py`).
2. **Modification du `main.py` hote** (ou factory app) pour appeler cette fonction.
3. **Configuration** — variables d'env documentees, `.env.example` mis a jour si present.
4. **Migrations** — instruction ou script pour `alembic upgrade head` (chemins adaptes si besoin).
5. **Note d'integration** — fichier `INTEGRATION-FLORA.md` a la racine du projet hote resumant : scenario choisi, prefixe, auth, DB, points de vigilance.
6. **Checklist** — cocher les items de `docs/integration-module/06-verification.md`.

---

## Ordre de travail recommande

1. Analyser l'app hote (routes, auth, DB, static) — remplir la grille de `02-analyse-application-hote.md`.
2. Choisir et valider le scenario (`05-scenarios-et-decisions.md`).
3. Copier ou referencer le code FLORA dans le monorepo hote.
4. Creer `monter_flora()` : lifespan (admin seed optionnel), middleware, routers, static, exception handlers.
5. Aligner `RACINE_PROJET` / chemins templates si la structure differe.
6. Executer migrations et tester login + une page par module.
7. Verifier la checklist `06-verification.md`.

---

## Fichiers FLORA critiques a ne pas oublier

| Element | Chemin |
|---------|--------|
| Point d'entree actuel | `backend/app/main.py` |
| Middleware auth | `backend/app/core/auth_middleware.py` |
| Config + RACINE_PROJET | `backend/app/core/config.py` |
| DB session | `backend/app/core/database.py` |
| Templates Jinja2 | `backend/app/templates/` |
| Traductions UI | `backend/app/traductions/es.py` |
| CSS / uploads | `static/` |
| Migrations | `backend/alembic/`, `alembic.ini` |
| Registre modules nav | `backend/app/modules/base/registre_modules.py` |

---

## En cas de blocage

- **Collision table `utilisateurs`** → preferer scenario D (base separee) ou B avec table dediee FLORA.
- **Collision `/static`** → mount sous `{prefix}/static` et patcher les templates.
- **Middleware global trop agressif** → limiter `AuthMiddleware` aux chemins sous le prefixe FLORA (refactor du middleware necessaire).
- **Monorepo sans `backend.app`** → renommer le package ou ajuster PYTHONPATH dans le demarrage hote.

Demande validation humaine avant toute modification destructive (suppression de routes hote, fusion de tables users, force push, etc.).
