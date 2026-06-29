# 02 — Analyse de l'application hote

Avant toute modification, l'IA (ou l'integrateur) doit inventorier l'application cible et remplir ce document.

## Grille d'analyse

### 1. Structure du projet hote

| Question | Reponse |
|----------|---------|
| Chemin racine du projet hote | |
| Point d'entree FastAPI (`main.py` ou factory) | |
| Organisation des packages Python | |
| Presence d'un monorepo / workspaces | |
| Comment le PYTHONPATH est configure au demarrage | |

### 2. Routes existantes — collisions potentielles

FLORA reserve ces chemins si monte a la racine :

```
/                          (accueil FLORA)
/login, /logout
/contacts
/vehicules, /imprimantes, /ordinateurs
/vehicules/*, /imprimantes/*, /ordinateurs/*
/admin/users
/admin/vehicules, /admin/vehicules/configuracion
/admin/imprimantes, /admin/ordinateurs
/api/v1/vehicules, /api/v1/imprimantes, /api/v1/ordinateurs
/api/v1/recherche
/partials/recherche
/static/*
```

| Question | Reponse |
|----------|---------|
| L'hote utilise-t-il `/` ? | |
| L'hote utilise-t-il `/login` ? | |
| L'hote utilise-t-il `/admin/*` ? | |
| L'hote utilise-t-il `/api/v1/*` ? | |
| L'hote monte-t-il `/static` ? | |
| Prefixe URL libre propose pour FLORA | ex. `/flora`, `/ressources` |

### 3. Authentification

| Question | Reponse |
|----------|---------|
| Auth existante ? | oui / non |
| Type | JWT cookie / JWT header / session / OAuth / autre |
| Table utilisateurs existante ? | nom de table, champs |
| Roles existants | mapping possible vers `admin` / `user` ? |
| Middleware auth global deja present ? | |
| Nom du cookie de session hote | risque de conflit avec `flora_token` |
| Pages login de l'hote | URL |

**Forme attendue par FLORA pour `request.state.utilisateur`** :

```python
# Objet avec au minimum :
utilisateur.id          # int
utilisateur.email       # str — identifiant 3 chiffres dans FLORA natif
utilisateur.nom         # str | None
utilisateur.role        # "admin" | "user"
utilisateur.est_actif   # bool
```

### 4. Base de donnees

| Question | Reponse |
|----------|---------|
| Moteur | SQLite / PostgreSQL / autre |
| `DATABASE_URL` actuelle | |
| SQLAlchemy deja utilise ? | version, pattern session |
| Alembic deja utilise ? | chemin, historique de revisions |
| Table `utilisateurs` deja presente ? | |
| Strategie retenue | meme DB / DB separee / schema separe (non supporte nativement) |

**Tables FLORA a creer** (via migrations 001-015) :

- `utilisateurs`
- `vehicules`, `vehicule_journaux`, `vehicule_immobilisations`, `vehicules_configuration`
- `imprimantes`, `imprimante_evenements`
- `ordinateurs`, `ordinateur_evenements`

### 5. Templates et assets

| Question | Reponse |
|----------|---------|
| Jinja2 deja configure ? | |
| Dossier templates hote | |
| StaticFiles deja monte ? | chemin |
| CDN / bundler frontend ? | |
| Conflit CSS avec FLORA ? | |

### 6. Deploiement et environnement

| Question | Reponse |
|----------|---------|
| Hebergeur | local / Vercel / Docker / autre |
| Variables d'env existantes | lister |
| Stockage fichiers | local / S3 / Vercel Blob |
| CI/CD | migrations automatiques ? |

### 7. Dependances Python

Comparer `requirements.txt` de FLORA avec celles de l'hote :

```
fastapi, uvicorn, sqlalchemy, alembic, pydantic-settings,
jinja2, python-multipart, psycopg, httpx, python-jose, bcrypt, email-validator
```

| Question | Reponse |
|----------|---------|
| Versions compatibles ? | |
| Conflits de versions connus ? | |

## Sortie attendue de l'analyse

1. **Scenario recommande** (A, B, C ou D — voir `05-scenarios-et-decisions.md`)
2. **Liste des collisions** de routes a resoudre
3. **Decision auth** : garder FLORA / adapter hote / hybride
4. **Decision DB** : migrations sur quelle base
5. **Plan de prefixe URL** et impact sur templates/static

Ne pas commencer le codage tant que ces points ne sont pas documentes dans `INTEGRATION-FLORA.md` du projet hote.
