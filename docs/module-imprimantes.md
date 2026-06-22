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

## Statut deduit des evenements

Le statut n'est **pas saisi manuellement**. Il est calcule a partir du dernier evenement impactant l'etat :

| Dernier evenement | Statut |
|-------------------|--------|
| `panne` | En panne |
| `maintenance` ou `reparation` | En maintenance |
| `maintenance_terminee` ou autre | OK |

Les evenements `compteur` et `toner` ne modifient pas le statut.

## Types d'evenements

| Type | Effet |
|------|-------|
| compteur | Met a jour `compteur_pages` (obligatoire) |
| toner | Met a jour `date_dernier_toner`, compteur optionnel |
| maintenance | Demarre une maintenance (statut -> maintenance) |
| maintenance_terminee | Termine maintenance/reparation (statut -> OK, date maintenance) |
| panne | Signale une averia (statut -> panne) |
| reparation | Reparation en cours (statut -> maintenance) |

Le compteur ne peut pas diminuer.

## Routes web

| Route | Description |
|-------|-------------|
| `GET /imprimantes` | Liste + modal evenement |
| `GET /imprimantes/{id}/historique` | Historique |
| `POST /imprimantes/{id}/evenement` | Enregistrer un evenement |
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

## Donnees de demonstration

```powershell
python scripts/seed_donnees.py
```

Insere 5 imprimantes fictives (si la table est vide) : IMP-RECEP, IMP-ADMIN, IMP-ALM (averia), IMP-SALA (mantenimiento), IMP-TALLER.
