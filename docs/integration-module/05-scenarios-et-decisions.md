# 05 — Scenarios et decisions d'integration

Choisir **un scenario** avant de coder. Documenter le choix dans `INTEGRATION-FLORA.md` du projet hote.

---

## Scenario A — Sous-application avec prefixe URL (recommande)

**Principe** : FLORA vit sous `/flora` (ou autre prefixe), auth FLORA native, meme base de donnees ou base dediee.

| Avantage | Inconvenient |
|----------|--------------|
| Isole les routes de l'hote | Refactor des chemins dans templates et middleware |
| Collision minimale | URLs longues (`/flora/vehicules`) |
| Auth FLORA autonome | Deux systemes de login possibles (hote + FLORA) |

**Travail principal** :
- Creer `monter_flora(app, prefix="/flora")`
- Adapter `AuthMiddleware` : chemins publics et redirect `/flora/login`
- Injecter `prefixe_url` dans templates ou remplacer les liens `/static`, `/vehicules`, etc.
- Lien depuis le menu hote vers `/flora/`

**Quand choisir** : hote deja mature avec ses propres routes `/`, `/login`, `/admin`.

---

## Scenario B — Auth unique de l'hote

**Principe** : Pas de `AuthMiddleware` FLORA ni de table `utilisateurs` FLORA (ou table ignoree). L'hote fournit `request.state.utilisateur`.

| Avantage | Inconvenient |
|----------|--------------|
| Un seul login pour l'utilisateur | Adaptateur a maintenir |
| Pas de compte `001/admin123` | Mapping roles peut etre imperfect |
| Coherence SSO possible | Pages `/admin/users` FLORA a retirer ou desactiver |

**Travail principal** :
- Middleware hote → adaptateur qui mappe l'utilisateur hote vers l'interface FLORA
- Desactiver `router_auth` (login FLORA) et `router_admin` users
- Desactiver seed admin lifespan
- Verifier `affichage.py` et filtres role `user` (vehicule assigne)

**Forme minimale utilisateur** :

```python
class UtilisateurFloraAdaptateur:
    id: int
    email: str      # identifiant affiche ; peut etre l'ID hote converti
    nom: str | None
    role: str       # "admin" | "user"
    est_actif: bool = True
```

**Quand choisir** : l'hote a deja auth + gestion users et on veut une experience unifiee.

---

## Scenario C — Montage a la racine (FLORA devient l'app principale)

**Principe** : FLORA occupe `/`, l'hote deplace ses routes ailleurs ou n'a que l'API FLORA.

| Avantage | Inconvenient |
|----------|--------------|
| Peu de modifications FLORA | L'hote doit ceder la racine |
| Templates/static inchanges | Rare en pratique |

**Travail principal** :
- Inclure routers FLORA sans prefixe (comme `main.py` actuel)
- Deplacer ou supprimer les routes conflictuelles de l'hote

**Quand choisir** : l'hote est un coquille vide ou un proxy, FLORA est le produit principal.

---

## Scenario D — Base de donnees separee (micro-module)

**Principe** : FLORA sur prefixe URL + **base PostgreSQL/SQLite dediee**, auth FLORA ou B.

| Avantage | Inconvenient |
|----------|--------------|
| Zero collision de tables | Deux `DATABASE_URL` à gerer |
| Migrations independantes | Refactor `database.py` obligatoire |
| Isolation forte | Pas de jointures avec donnees hote |

**Travail principal** :
- Extraire engine/session FLORA (ne pas partager `SessionLocal` hote)
- `FLORA_DATABASE_URL` + second engine
- Alembic separe ou revisions dans un second historique

**Quand choisir** : hote a deja une table `utilisateurs` incompatible, ou politique d'isolation stricte.

---

## Matrice de decision rapide

| Situation | Scenario |
|-----------|----------|
| App hote avec son propre `/` et login | **A** |
| SSO / users centralises dans l'hote | **B** (+ A pour prefixe) |
| Nouveau projet, FLORA = coeur metier | **C** |
| Table users existante incompatible | **D** ou **B** |
| Deploiement Vercel, une seule DB Postgres | **A** ou **B** (meme DB) |

---

## Decisions complementaires

### Dashboard FLORA (`/`)

| Option | Description |
|--------|-------------|
| Garder | Accueil FLORA a `/flora/` |
| Remplacer | Rediriger vers accueil hote ; entree FLORA = `/flora/vehicules` |
| Fusionner | Extraire widgets du dashboard dans l'UI hote (effort eleve) |

### Gestion des utilisateurs FLORA

| Option | Description |
|--------|-------------|
| Garder `/admin/users` | Scenario A ou C |
| Desactiver | Scenario B — users geres par l'hote |
| Synchroniser | Script periodique hote → `utilisateurs` (custom, non fourni) |

### Modules a activer

Editer `registre_modules.py` pour desactiver imprimantes ou ordinateurs si non necessaires :

```python
ModuleRessource(id="imprimantes", ..., actif=False),
```

### Stockage fichiers

| Environnement | Configuration |
|---------------|---------------|
| Dev local | `static/uploads/` automatique |
| Vercel | `BLOB_READ_WRITE_TOKEN` ou OIDC + `BLOB_STORE_ID` |
| Hote S3 | Refactor `stockage_fichiers.py` (non fourni) |

---

## Livrable decision

Creer dans le projet hote :

```markdown
# INTEGRATION-FLORA.md

## Scenario retenu
A — prefixe /flora

## Auth
FLORA native, cookie flora_token

## Base de donnees
Meme PostgreSQL, migrations FLORA 001-015

## Prefixe URL
/flora

## Routes hote impactees
Aucune (prefixe isole)

## Points ouverts
- [ ] Lien menu hote vers /flora/
- [ ] Logo entreprise partage ou FLORA seul
```
