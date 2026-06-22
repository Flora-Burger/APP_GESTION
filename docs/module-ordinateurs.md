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

## Statut deduit des evenements

Le statut n'est **pas saisi manuellement** en liste publique. Il est calcule :

| Dernier evenement impactant | Statut |
|-----------------------------|--------|
| `panne` | En panne |
| `entretien`, `intervention_technique` | En maintenance |
| `maintenance_terminee` ou aucun blocage | OK |

L'evenement `changement_utilisateur` met a jour l'utilisateur assigne sans bloquer l'equipement.

## Types d'evenements

| Type | Effet |
|------|-------|
| changement_utilisateur | Change ou retire l'utilisateur assigne |
| entretien | Maintenance en cours |
| intervention_technique | Intervention technique en cours |
| maintenance_terminee | Fin de maintenance (retour a OK) |
| panne | Equipement indisponible |

## Routes web

| Route | Description |
|-------|-------------|
| `GET /ordinateurs` | Liste + modal evenement |
| `GET /ordinateurs/{id}/historique` | Historique |
| `POST /ordinateurs/{id}/evenement` | Enregistrer un evenement |
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

## Donnees de demonstration

Le script `scripts/seed_donnees.py` insere 6 ordinateurs fictifs (PC-RECEP, PC-ADMIN, PC-ALM, PC-TALLER, PC-SALA, PORT-JEFE) avec historique.
