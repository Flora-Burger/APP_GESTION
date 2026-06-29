# Integration du module FLORA dans une application existante

Ce dossier contient **toutes les instructions** pour qu'une IA (Cursor, Claude, etc.) integre le projet **APP_GESTION / FLORA** comme module d'une application FastAPI deja en place.

## Contenu

| Fichier | Role |
|---------|------|
| [PROMPT-CURSOR.md](PROMPT-CURSOR.md) | **Prompt principal** a copier-coller dans Cursor pour lancer l'integration |
| [01-vue-ensemble.md](01-vue-ensemble.md) | Ce qu'est le module, stack, structure des dossiers |
| [02-analyse-application-hote.md](02-analyse-application-hote.md) | Questions et inventaire a faire sur l'app cible avant d'integrer |
| [03-plan-integration.md](03-plan-integration.md) | Etapes detaillees d'integration (phases 0 a 6) |
| [04-reference-technique.md](04-reference-technique.md) | Routes, tables, variables d'env, fichiers critiques |
| [05-scenarios-et-decisions.md](05-scenarios-et-decisions.md) | 4 scenarios d'integration et leurs compromis |
| [06-verification.md](06-verification.md) | Checklist de tests apres integration |

## Utilisation rapide

### Pour un humain

1. Lire [05-scenarios-et-decisions.md](05-scenarios-et-decisions.md) et choisir un scenario (A recommande pour debuter).
2. Repondre aux questions de [02-analyse-application-hote.md](02-analyse-application-hote.md).
3. Ouvrir Cursor dans le **projet hote** (ou un monorepo contenant les deux projets).
4. Copier le contenu de [PROMPT-CURSOR.md](PROMPT-CURSOR.md) et completer les sections `[A REMPLIR]`.

### Pour une IA

Lire dans l'ordre :

1. `PROMPT-CURSOR.md` (mission et contraintes)
2. `01-vue-ensemble.md`
3. `02-analyse-application-hote.md` (apres analyse du code hote)
4. `03-plan-integration.md` (plan d'execution)
5. `04-reference-technique.md` (reference pendant le codage)
6. `06-verification.md` (validation finale)

## Documentation complementaire du projet

- [../architecture.md](../architecture.md) — architecture interne FLORA
- [../authentification.md](../authentification.md) — auth JWT + roles
- [../module-vehicules.md](../module-vehicules.md)
- [../module-imprimantes.md](../module-imprimantes.md)
- [../module-ordinateurs.md](../module-ordinateurs.md)

## Important

FLORA n'est **pas** un package pip installe. C'est une application FastAPI autonome dont le code doit etre **monte** (routers, middleware, templates, static, migrations) dans l'application hote. Le travail d'integration depend fortement de l'architecture de l'hote (routes, auth, base de donnees).
