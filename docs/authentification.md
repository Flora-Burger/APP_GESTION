# Authentification FLORA

## Vue d'ensemble

- Connexion par **identifiant numerique a 3 chiffres** (000-999) + mot de passe
- Mots de passe hashes avec **bcrypt**
- Session via **cookie HTTP-only** contenant un **JWT**
- Roles : `admin` | `user`
- Aucune inscription publique

## Compte administrateur par defaut

Cree automatiquement au demarrage si absent :

| Champ | Valeur |
|-------|--------|
| Identifiant | 001 |
| Mot de passe | admin123 |

**Changez ce mot de passe en production.**

## Routes publiques

- `/login`
- `/static/*`
- `/docs`, `/redoc`, `/openapi.json`

Toutes les autres routes sont protegees par le middleware `AuthMiddleware`.

## Routes admin (role admin requis)

### Utilisateurs

- `GET /admin/users` - Liste, creation et modification de comptes (modals). La liste affiche l'**identifiant** et le **nombre**.
- `POST /admin/users` - Creer user ou admin (identifiant, nombre, mot de passe, role)
- `POST /admin/users/{id}/modifier` - Modifier identifiant, nombre, mot de passe (optionnel), role
- `POST /admin/users/{id}/toggle` - Activer/desactiver
- `POST /admin/users/{id}/supprimer` - Supprimer

### Vehicules

Voir [module-vehicules.md](module-vehicules.md) section Administration.

## Modele `utilisateurs`

| Champ | Type |
|-------|------|
| id | Integer |
| email | String(3) (unique) - identifiant numerique sur 3 chiffres |
| mot_de_passe_hash | String |
| nom | String (nombre affiche, optionnel si cuenta antigua) |
| role | admin \| user |
| est_actif | Boolean |
| cree_le | DateTime |

## Configuration (.env)

```
JWT_SECRET=changez-cette-cle-secrete-en-production-flora
JWT_EXPIRATION_MINUTES=480
COOKIE_SECURE=false
```

## Securite

- Verification des permissions **cote backend uniquement**
- API : 401 si non authentifie, 403 si acces refuse
- Web : redirection vers `/login` si non authentifie
- Impossible de supprimer/desactiver le dernier admin actif
- Impossible de desactiver ou supprimer son propre compte depuis l'admin
- Un administrateur peut modifier son propre compte (identifiant, nom, mot de passe, role avec protection du dernier admin)
- Changement de role user/admin avec protection du dernier admin actif
