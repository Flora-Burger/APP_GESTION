# Module Imprimantes

## Objectif

Gestion simple des imprimantes pour une PME : compteur de pages, toner, maintenance et historique d'evenements.

## Modele de donnees

### Table `imprimantes`

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant |
| nom | String(100) | Nom / identifiant (unique) |
| modele | String(150) | Modele |
| localisation | String(200) | Emplacement |
| statut | String | `ok`, `panne`, `maintenance` |
| compteur_pages | Integer | Compteur total (source d'usage) |
| date_dernier_toner | Date nullable | Dernier remplacement toner |
| date_derniere_maintenance | Date nullable | Derniere maintenance |
| cree_le | DateTime | Date de creation |

### Table `imprimante_evenements`

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant |
| imprimante_id | FK | Reference imprimante |
| date_evenement | Date | Date de l'evenement |
| type_evenement | String | `compteur`, `toner`, `maintenance`, `maintenance_terminee`, `panne`, `reparation` |
| compteur_pages | Integer nullable | Valeur compteur si applicable |
| commentaire | Text nullable | Note libre |

## Statut (admin)

Le champ `statut` est la **source de verite**, modifie par l'admin via pastille cliquable : OK, Mantenimiento, Averia (`panne` en base).

Champs admin supplementaires (migration 013) : `fecha_compra`, `tipo_tinta`, `facture_url`.

## Types d'evenements (admin uniquement)

| Type | Effet |
|------|-------|
| toner | Met a jour `date_dernier_toner` |
| reparation | Historique uniquement |

Les utilisateurs non-admin voient la liste en **lecture seule** (sans compteur ni boutons d'action).

## Routes web

| Route | Description |
|-------|-------------|
| `GET /imprimantes` | Liste + modal evenement |
| `GET /imprimantes/{id}/historique` | Historique |
| `POST /imprimantes/{id}/evenement` | Enregistrer un evenement (admin) |
| `POST /admin/imprimantes/{id}/statut` | Modifier le statut (admin) |
| `GET /admin/imprimantes` | Admin : CRUD imprimantes |

## Routes API

| Methode | Route | Description |
|---------|-------|-------------|
| GET | `/api/v1/imprimantes` | Liste avec filtres |
| GET | `/api/v1/imprimantes/{id}` | Detail + historique |
| POST | `/api/v1/imprimantes` | Creer |
| PUT | `/api/v1/imprimantes/{id}` | Modifier donnees maitres |
| POST | `/api/v1/imprimantes/{id}/evenements` | Enregistrer evenement |

## Migration

- `006` : tables `imprimantes` et `imprimante_evenements`
- `013` : `fecha_compra`, `facture_url`, `tipo_tinta`

## Donnees de demonstration

```powershell
python scripts/seed_donnees.py
```

Insere 5 imprimantes fictives (si la table est vide) : IMP-RECEP, IMP-ADMIN, IMP-ALM (averia), IMP-SALA (mantenimiento), IMP-TALLER.
