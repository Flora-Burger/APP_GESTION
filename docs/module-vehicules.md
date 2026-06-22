# Module Vehicules

## Objectif

Gerer et consulter les vehicules de fonction avec suivi quotidien d'utilisation, consommation, kilometrage et conformite ITV.

## Modele de donnees

### Table `vehicules` (donnees maitres)

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant unique |
| matricule | String(20) | Immatriculation (unique, admin) |
| marque | String(100) | Marque (legacy, utilise pour affichage modele) |
| modele | String(100) | Modele (admin) |
| date_expiration_itv | Date | Date d'expiration du controle technique (obligatoire) |
| kilometrage_actuel | Integer | Kilometrage actuel du compteur (obligatoire a la creation) |
| photo_url | String | Legacy, non affiche |
| consommation_moyenne | Decimal | Legacy, non affiche |

### Table `vehicule_journaux` (historique quotidien)

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant |
| vehicule_id | FK | Reference vehicule |
| date_jour | Date | Date (unique par vehicule) |
| utilisateur | String nullable | Utilisateur du jour (null = Libre) |
| actif | Boolean | Utilisation active du jour |
| kilometrage_actuel | Integer | Snapshot du km actuel apres mise a jour |
| kilometrage_jour | Integer | Kilometres parcourus ce jour (calcule) |
| consommation_jour | Decimal | Litres consommes ce jour |
| cout_carburant_jour | Decimal | Cout carburant du jour (EUR) |

**Contrainte** : `UNIQUE(vehicule_id, date_jour)` - historique preserve.

## Kilometrage

### Saisie

- **Creation admin** : kilometrage actuel initial obligatoire.
- **Actualisation du jour** : l'utilisateur saisit uniquement le **kilometraje actual** (lecture compteur).

### Calcul automatique (backend)

`kilometrage_jour += nouveau_kilometrage_actuel - ancien_kilometrage_actuel`

Le kilometrage du jour n'est jamais saisi manuellement. Chaque entree journal conserve un snapshot `kilometrage_actuel` et le cumul `kilometrage_jour` du jour.

### Validation

- Valeurs entieres positives ou nulles.
- Interdiction d'enregistrer un kilometrage inferieur au kilometrage actuel du vehicule.

## Statuts calcules

### Statut vehicule (filtre uniquement)

- `utilisateur` null ou vide sur l'utilisation active → **Libre** / **Disponible**
- Utilisation active du jour → **Occupe**
- ITV expiree → **No disponible** (badge cliquable, meme style que Ocupado ; ouvre la modal ITV ; assignation impossible)
- Immobilisation active au garage → **En taller** (affichage prioritaire, filtre `au_garage`)

Assignation via badge **Disponible** (modal oui/non) : l'utilisateur connecte devient utilisateur du jour.
Liberation via badge **Ocupado** (modal oui/non).

### Journal quotidien

Plusieurs entrees par jour et par vehicule si les utilisateurs sont differents (champ `actif` sur chaque entree).
Une seule utilisation active a la fois par vehicule et par jour.

La liberation d'un vehicule desactive l'entree de l'utilisateur (`actif = false`) sans effacer ses donnees. Sur la fiche, le **kilometraje del dia**, les **litres** et le **cout** affiches sont la **somme** de toutes les utilisations du jour (tous utilisateurs confondus). Chaque utilisateur conserve sa propre entree journal pour l'historique.

L'actualisation des donnees du jour ne demande plus l'utilisateur : il est fixe par l'assignation.

Seuls l'utilisateur assigne au vehicule (utilisateur du jour) et les administrateurs peuvent actualiser les donnees du jour.

### Immobilisation au garage

Table `vehicule_immobilisations` : motif, garage, dates, commentaire.

Actions sur la fiche vehicule :

- **Enviar al taller** : ouvre une modal (motif, garage, dates, commentaire)
- Icone **info** a cote du badge **En taller** : affiche les details de l'immobilisation en modal
- **Volver al servicio** : cloture l'immobilisation (confirmation simple)

### Statut ITV (affichage couleur)

| Couleur | Condition |
|---------|-----------|
| Vert | ITV valide (> 30 jours) |
| Orange | ITV expire dans moins de 30 jours |
| Rouge | ITV expiree |

Le badge ITV (Valida, Proxima a vencer, Vencida) est cliquable et ouvre une modal pour consulter l'etat actuel et modifier la date d'expiration (`POST /vehicules/{id}/itv`).

## Champs affiches sur la fiche

- Matricula (immatriculation)
- Modelo
- Usuario del dia
- Kilometraje actual
- Kilometraje del dia (cumul de tous les utilisateurs du jour)
- Litros del repostaje hoy (cumul du jour)
- Coste del repostaje hoy (cumul du jour)
- ITV avec date de validite

## Modification des donnees

Modifiables par l'utilisateur assigne (modal **Actualizar datos del dia**) :

- Kilometraje actual (compteur) — le km du jour est calcule automatiquement
- Litres consommes aujourd'hui (session de l'utilisateur)
- Cout carburant aujourd'hui (session de l'utilisateur)

La date ITV se modifie via la modal ouverte en cliquant sur le badge ITV (plus dans l'actualisation du jour).

L'utilisateur du jour est fixe par l'assignation (badge Disponible/Ocupado).

Lecture seule (admin) : immatriculation, modele.

## Vue Historique

Route : `GET /vehicules/{id}/historique`

- **Kilometraje actual** affiche au-dessus du tableau.
- Section **Uso diario** : date, utilisateur, kilometraje del dia, litres, cout.

Deux sections :

1. **Envios al taller** : chaque immobilisation (date debut, garage, motif, date retour ou « En curso »)
2. **Uso diario** : historique des journaux (uniquement les jours avec au moins un kilometrage, litres ou cout enregistre ; les assignations sans saisie n'apparaissent pas)

Barre de recherche dediee (utilisateur, date) : filtre uniquement les donnees de l'historique (journaux et immobilisations par date). La recherche par utilisateur ne concerne que l'usage quotidien.

Les immobilisations sont triees par date de debut decroissante.

## Filtres disponibles

| Filtre | Parametre | Valeurs |
|--------|-----------|---------|
| Estado | `statut` | libre, occupe, au_garage |
| ITV | `itv` | valide, expire_bientot, expiree |
| Kilometraje del dia | `km_jour` | moins_30 (< 30), entre_30_60 (30-59), entre_60_120 (60-120), plus_120 (> 120) |
| Busqueda | `recherche` | Matricule, modele, utilisateur du jour (pas l'historique) |

## Endpoints API

| Methode | Route | Description |
|---------|-------|-------------|
| GET | `/api/v1/vehicules` | Liste avec filtres |
| GET | `/api/v1/vehicules/{id}` | Detail + historique |
| POST | `/api/v1/vehicules` | Creer un vehicule |
| POST | `/api/v1/vehicules/{id}/journaux` | Enregistrer/mettre a jour donnees du jour |

## Validation carburant

Les champs **litres du plein** et **cout du plein** sont lies :

- Si litres > 0, le cout est obligatoire (> 0)
- Si cout > 0, les litres sont obligatoires (> 0)
- Validation cote serveur (Pydantic) et navigateur (JavaScript)

## Administration vehicules (admin uniquement)

Route : `GET /admin/vehicules`

| Action | Route | Champs |
|--------|-------|--------|
| Lister / creer | `GET/POST /admin/vehicules` | matricule, modele, kilometrage actuel, photo (optionnelle) |
| Modifier | `GET/POST /admin/vehicules/{id}/modifier` | matricule, modele, photo (fichier) |
| Supprimer | `POST /admin/vehicules/{id}/supprimer` | Confirmation navigateur |

Acces : lien **Gestion de vehiculos** visible uniquement sur `/vehicules` (admins).

- Photos uploadees dans `static/uploads/vehicules/`
- Remplacement : l'ancienne photo locale est supprimee
- Formats acceptes : JPG, PNG, WebP (max 5 Mo)
- La photo est visible immediatement sur la fiche vehicule (`/vehicules`)

## Photos

Resolution via `images_vehicules.py` et uploads admin :

- URL enregistree (upload admin ou legacy) en priorite
- Sinon catalogue par marque/modele
- Sinon image utilitaire generique

## Migrations

- `001` : tables initiales
- `002` : `date_expiration_itv`, `cout_carburant_jour`
- `005` : suppression colonne legacy `itv_valide`
- `008` : table `vehicule_immobilisations`
- `009` : journal `actif`, plusieurs utilisations/jour (utilisateurs differents)
- `010` : suppression des colonnes kilometrage (refactoring)
- `011` : `kilometrage_actuel` (vehicules), `kilometrage_actuel` et `kilometrage_jour` (journaux)

## Script de reinitialisation (tests)

Pour effacer les donnees du jour (journaux + immobilisations demarrees ce jour) :

```bash
VFLORA\Scripts\python.exe scripts\reinitialiser_journee.py
```

Option `--date AAAA-MM-JJ` pour une autre date. L'historique des jours precedents est conserve.
