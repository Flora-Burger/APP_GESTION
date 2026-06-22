"""Calcul du statut operationnel deduit des evenements."""

from backend.app.modules.ordinateurs.modeles import OrdinateurEvenement
from backend.app.modules.ordinateurs.schemas import StatutOrdinateur, TypeEvenement

_TYPES_ETAT: frozenset[str] = frozenset(
    {
        TypeEvenement.PANNE.value,
        TypeEvenement.ENTRETIEN.value,
        TypeEvenement.MAINTENANCE_TERMINEE.value,
        TypeEvenement.INTERVENTION_TECHNIQUE.value,
    }
)


_TYPES_MAINTENANCE: frozenset[str] = frozenset(
    {
        TypeEvenement.ENTRETIEN.value,
        TypeEvenement.INTERVENTION_TECHNIQUE.value,
    }
)


def _statut_selon_utilisateur(utilisateur_assigne: str | None) -> StatutOrdinateur:
    """Statut nominal par defaut."""
    _ = utilisateur_assigne
    return StatutOrdinateur.OK


def calculer_statut_depuis_evenements(
    evenements: list[OrdinateurEvenement],
    utilisateur_assigne: str | None,
) -> StatutOrdinateur:
    """Deduit l'etat a partir du dernier evenement impactant le statut."""
    candidats = [e for e in evenements if e.type_evenement in _TYPES_ETAT]
    if not candidats:
        return _statut_selon_utilisateur(utilisateur_assigne)

    dernier = max(candidats, key=lambda e: (e.date_evenement, e.id))

    if dernier.type_evenement == TypeEvenement.PANNE.value:
        return StatutOrdinateur.EN_PANNE

    if dernier.type_evenement in _TYPES_MAINTENANCE:
        return StatutOrdinateur.EN_MAINTENANCE

    return _statut_selon_utilisateur(utilisateur_assigne)
