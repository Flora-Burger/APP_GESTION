# Architecture - App Gestion FLORA

## Vue d'ensemble

Application modulaire de gestion des ressources materielles de l'entreprise.

- **Code** : Python, noms et commentaires en francais
- **Interface utilisateur** : espagnol (fichier `backend/app/traductions/es.py`)
- **API** : REST FastAPI, prete pour deploiement cloud
- **UI web** : Jinja2 + HTMX

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Base de donnees (dev) | SQLite (`data/flora.db`) |
| Base de donnees (prod) | PostgreSQL (via `DATABASE_URL`) |
| Templates | Jinja2 |
| Interactivite | HTMX 2.x |
| Authentification | JWT (cookie HTTP-only) + bcrypt |

Voir [authentification.md](authentification.md) pour le systeme de comptes.

Pour integrer ce projet comme module dans une autre application FastAPI, voir [integration-module/](integration-module/README.md).

## Structure des dossiers

```
APP_GESTION/
├── VFLORA/                 # Environnement virtuel Python
├── backend/
│   ├── app/
│   │   ├── main.py         # Point d'entree
│   │   ├── core/           # Config, DB, dependances
│   │   ├── modules/        # Modules metier
│   │   ├── traductions/    # Textes UI en espagnol
│   │   └── templates/      # Templates Jinja2
│   └── alembic/            # Migrations
├── static/                 # CSS, images
├── scripts/                # Utilitaires (seed, etc.)
└── docs/                   # Documentation
```

## Flux de donnees

```
Navigateur
    |
    +-- Routes web (/ , /vehicules) --> Templates Jinja2
    |                                      |
    +-- Routes API (/api/v1/...) --------> Services metier
                                               |
                                          Repositories
                                               |
                                          Base de donnees
```

## Pattern modulaire

Chaque type de materiel est un module dans `backend/app/modules/` avec :

- `modeles.py` - Entites SQLAlchemy
- `schemas.py` - Schemas Pydantic
- `repository.py` - Acces aux donnees
- `service.py` - Logique metier
- `router_api.py` - Endpoints REST
- `router_web.py` - Pages web

Les modules actifs sont enregistres dans `modules/base/registre_modules.py` (vehicules, imprimantes, ordinateurs).

### Page d'accueil (tableau de bord)

La route `/` affiche un panel de control avec :

- Message de bienvenue et resume des alertes (somme des elements indisponibles : ITV vencida, averias et mantenimientos)
- Barre de recherche globale (HTMX)
- Les barres de recherche (accueil et listes) portent sur les donnees courantes du parc, pas sur l'historique (journaux passes, immobilisations, evenements)
- Cartes cliquables par module avec indicateurs : total, disponibles (vehicules) ou en servicio (autres modules), no disponible
- Pour les vehicules : chaque entree est comptee une seule fois ; disponible = libre, pas au garage et ITV non expiree ; le reste est no disponible (occupe, garage, ITV vencida)

Logique metier : `backend/app/modules/accueil/service.py`

Voir aussi :

- [module-vehicules.md](module-vehicules.md)
- [module-imprimantes.md](module-imprimantes.md)
- [module-ordinateurs.md](module-ordinateurs.md)

## Configuration

Variables d'environnement (fichier `.env`) :

| Variable | Description | Defaut |
|----------|-------------|--------|
| `NOM_ENTREPRISE` | Nom affiche dans l'en-tete | Grup CST & Batmar S.L. |
| `LOGO_URL` | Chemin du logo | /static/img/logo.png |
| `DATABASE_URL` | URL de connexion DB | sqlite:///./data/flora.db |
| `DEBUG` | Mode debug SQLAlchemy | true |

La page d'accueil (`/`) applique la classe `page-accueil` pour le hero (logo, nom d'entreprise). L'interface globale utilise une palette bleue dominante (`--couleur-primaire`); les icones des modules du tableau de bord conservent leur couleur verte (`--couleur-icone`).

## Interface mobile

L'application conserve la meme version sur ordinateur et mobile (une seule base de code). Sur ecrans <= 768px uniquement (`static/css/mobile.css`) :

- Filtres repliables via le bouton **Filtros** (`partials/bouton_ouvrir_filtres.html`).
- Badges de statut lisibles (texte colore) sur les cartes vehicules, imprimantes et ordinateurs.
- Menu lateral (hamburger) : accueil, modules, contacts ou admin, deconnexion.

Le bureau n'est pas modifie : les regles mobile sont isolees dans `mobile.css` ; `style.css` conserve la mise en page ordinateur d'origine.

## Demarrage

### Windows (pruebas rapidas)

Doble clic en `iniciar.bat` a la racine du projet. Le script libere le port 8000 si une ancienne instance Uvicorn l'occupe encore.

### Installation manuelle

```powershell
cd e:\FLORA\APP_GESTION
python -m venv VFLORA
.\VFLORA\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_donnees.py
uvicorn backend.app.main:app --reload
```

- Interface web : http://localhost:8000
- Documentation API : http://localhost:8000/docs

## Deploiement cloud

1. Configurer `DATABASE_URL` vers PostgreSQL
2. Executer `alembic upgrade head`
3. Servir avec Uvicorn/Gunicorn derriere un reverse proxy (Nginx)
4. L'API REST reste utilisable par un frontend SPA futur

## Ajout d'un nouveau module

1. Creer le dossier `backend/app/modules/<nom>/` avec la structure standard
2. Enregistrer le module dans `registre_modules.py`
3. Inclure les routers dans `main.py`
4. Creer migration Alembic si nouvelles tables
5. Ajouter traductions dans `traductions/es.py`
6. Documenter dans `docs/module-<nom>.md`
