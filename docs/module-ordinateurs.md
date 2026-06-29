# Module Ordinateurs

## Objectif

Gestion simple du parc informatique pour une PME : equipements, affectation, etat et historique d'interventions.

## Modele de donnees

### Table `ordinateurs`

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant |
| nom | String(100) | Nom de l'equipement (unique) |
| numero_serie | String(100) nullable | Numero de serie (unique si renseigne) |
| marque | String(100) | Marque |
| modele | String(150) | Modele |
| utilisateur_assigne | String(150) nullable | Utilisateur assigne |
| localisation | String(200) | Emplacement |
| statut | String | `ok`, `en_maintenance`, `en_panne` |
| systeme_exploitation | String nullable | OS |
| processeur | String nullable | Processeur |
| memoire_ram | String nullable | RAM |
| capacite_stockage | String nullable | Stockage |
| date_acquisition | Date nullable | Date d'achat |
| garantie | String nullable | Info garantie |
| cree_le | DateTime | Date de creation |

### Table `ordinateur_evenements`

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant |
| ordinateur_id | FK | Reference ordinateur |
| date_evenement | Date | Date de l'evenement |
| type_evenement | String | Voir types ci-dessous |
| commentaire | Text nullable | Note libre |
| utilisateur_responsable | String nullable | Utilisateur concerne ou responsable |

## Statut (admin)

Le champ `statut` est modifie directement par l'admin (OK, Mantenimiento, Averia). Champs admin supplementaires : `facture_url`, `licences` (JSON).

## Types d'evenements (admin uniquement)

| Type | Effet |
|------|-------|
| entretien | Historique maintenance |
| intervention_technique | Historique intervention |

L'assignation utilisateur passe par le formulaire admin, pas par evenement.

Les utilisateurs non-admin voient la liste complete en **lecture seule** avec section « Detalles tecnicos » depliable.

## Routes web

| Route | Description |
|-------|-------------|
| `GET /ordinateurs` | Liste (lecture seule user / admin avec actions) |
| `GET /ordinateurs/{id}/historique` | Historique |
| `POST /ordinateurs/{id}/evenement` | Enregistrer un evenement (admin) |
| `POST /admin/ordinateurs/{id}/statut` | Modifier le statut (admin) |
| `GET /admin/ordinateurs` | Admin : CRUD ordinateurs |

## Routes API

| Methode | Route | Description |
|---------|-------|-------------|
| GET | `/api/v1/ordinateurs` | Liste avec filtres |
| GET | `/api/v1/ordinateurs/{id}` | Detail + historique |
| POST | `/api/v1/ordinateurs` | Creer |
| PUT | `/api/v1/ordinateurs/{id}` | Modifier donnees maitres |
| POST | `/api/v1/ordinateurs/{id}/evenements` | Enregistrer evenement |

## Migration

- `007` : tables `ordinateurs` et `ordinateur_evenements`
- `013` : `facture_url`, `licences` (JSON)

## Donnees de demonstration

Le script `scripts/seed_donnees.py` insere 6 ordinateurs fictifs (PC-RECEP, PC-ADMIN, PC-ALM, PC-TALLER, PC-SALA, PORT-JEFE) avec historique.
