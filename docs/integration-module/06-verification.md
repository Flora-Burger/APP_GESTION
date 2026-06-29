# 06 — Verification post-integration

Cocher chaque item apres integration dans l'application hote.

## Demarrage

- [ ] L'application hote demarre sans erreur d'import
- [ ] `alembic upgrade head` (FLORA) s'execute sans erreur
- [ ] Les tables FLORA existent en base
- [ ] Aucune regression au demarrage des routes hote existantes

## Authentification

- [ ] Route login FLORA accessible (ou login hote redirige correctement)
- [ ] Connexion admin fonctionne (`001` / `admin123` si seed actif, ou compte hote mappe)
- [ ] Cookie auth pose (`flora_token` ou nom configure)
- [ ] Deconnexion fonctionne
- [ ] Utilisateur non connecte → redirect login (web) ou 401 (API)
- [ ] Role `user` ne peut pas acceder a `/admin/*` (ou `/flora/admin/*`)
- [ ] Pas de conflit de cookie avec l'auth hote

## Navigation et static

- [ ] CSS charges (`style.css`, `mobile.css`) — pas de 404
- [ ] Logo affiche
- [ ] Menu lateral mobile fonctionne (≤768px)
- [ ] Liens internes FLORA pointent vers le bon prefixe
- [ ] HTMX charge (CDN unpkg) et recherches partielles fonctionnent

## Module vehicules

- [ ] `GET /vehicules` (ou prefixe) affiche la liste
- [ ] Filtres et cartes s'affichent (mobile + bureau)
- [ ] Donnees du jour / ITV modifiables (admin ou user assigne)
- [ ] Seguro y talleres visibles dans infos flotte
- [ ] Clic adresse taller → ouvre Google Maps
- [ ] Admin : `/admin/vehicules` CRUD
- [ ] Admin : `/admin/vehicules/configuracion` seguro/talleres
- [ ] Historique vehicule accessible
- [ ] Upload photo vehicule (si teste)

## Module imprimantes

- [ ] Liste imprimantes accessible
- [ ] Historique et evenements
- [ ] Admin CRUD + factures si applicable

## Module ordinateurs

- [ ] Liste ordinateurs accessible
- [ ] Licences et details techniques
- [ ] Admin CRUD

## Accueil et contacts

- [ ] Dashboard `/` (ou `/flora/`) : cartes modules + compteurs
- [ ] Recherche globale HTMX
- [ ] Page `/contacts` : admins et utilisateurs

## API REST

- [ ] `GET /api/v1/vehicules` avec auth → 200
- [ ] Sans auth → 401
- [ ] `GET /docs` ou OpenAPI hote toujours accessible si requis

## Roles

- [ ] Admin voit tous les vehicules
- [ ] User voit uniquement son vehicule assigne (si applicable)
- [ ] User mobile redirige depuis accueil vers vehicules (comportement FLORA)

## Production (si deploye)

- [ ] `JWT_SECRET` personnalise (pas la valeur par defaut)
- [ ] `COOKIE_SECURE=true` en HTTPS
- [ ] PostgreSQL configure (`DATABASE_URL`)
- [ ] Uploads : Blob ou stockage hote fonctionnel
- [ ] Mot de passe admin par defaut change

## Documentation

- [ ] `INTEGRATION-FLORA.md` cree dans le projet hote
- [ ] `.env.example` mis a jour
- [ ] Equipe informee du prefixe URL et du scenario auth

## Commandes de test rapides

```bash
# Migrations
alembic upgrade head

# Demarrage (adapter selon hote)
uvicorn backend.app.main:app --reload

# Test API (avec cookie de session)
curl -b "flora_token=..." http://localhost:8000/api/v1/vehicules
```

## En cas d'echec

| Symptome | Piste |
|----------|-------|
| 404 sur CSS | Mount static ou prefixe templates |
| Redirect loop login | Chemins publics middleware incomplets |
| 500 sur toutes pages FLORA | DB non migree ou session DB incorrecte |
| Templates vides / erreur Jinja | Chemin `RACINE_PROJET` incorrect |
| Import `backend.app` | PYTHONPATH ou renommage package |
| 401 API alors que web OK | Cookie non envoye ; verifier `COOKIE_AUTH_NOM` |
