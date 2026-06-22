"""Calcul du statut operationnel deduit des evenements."""

from backend.app.modules.imprimantes.modeles import ImprimanteEvenement
from backend.app.modules.imprimantes.schemas import StatutImprimante, TypeEvenement

_TYPES_ETAT: frozenset[str] = frozenset(
    {
        TypeEvenement.PANNE.value,
        TypeEvenement.MAINTENANCE.value,
        TypeEvenement.REPARATION.value,
        TypeEvenement.MAINTENANCE_TERMINEE.value,
    }
)


def calculer_statut_depuis_evenements(
    evenements: list[ImprimanteEvenement],
) -> StatutImprimante:
    """Deduit l'etat a partir du dernier evenement impactant le statut."""
    candidats = [e for e in evenements if e.type_evenement in _TYPES_ETAT]
    if not candidats:
        return StatutImprimante.OK

    dernier = max(candidats, key=lambda e: (e.date_evenement, e.id))

    if dernier.type_evenement == TypeEvenement.PANNE.value:
        return StatutImprimante.PANNE

    if dernier.type_evenement in (
        TypeEvenement.MAINTENANCE.value,
        TypeEvenement.REPARATION.value,
    ):
        return StatutImprimante.MAINTENANCE

    return StatutImprimante.OK
