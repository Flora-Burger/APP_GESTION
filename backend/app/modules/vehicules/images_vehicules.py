"""Resolution des images publiques par marque et modele."""

from backend.app.modules.vehicules.modeles import Vehicule

# Images publiques (Unsplash) associees aux modeles de la flotte
IMAGES_PAR_MODELE: dict[tuple[str, str], str] = {
    ("renault", "kangoo"): (
        "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=600&auto=format"
    ),
    ("peugeot", "partner"): (
        "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&auto=format"
    ),
    ("ford", "transit"): (
        "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=600&auto=format"
    ),
    ("citroen", "berlingo"): (
        "https://images.unsplash.com/photo-1605893477799-b99e3bfdfabe?w=600&auto=format"
    ),
    ("toyota", "proace"): (
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=600&auto=format"
    ),
}

IMAGE_UTILITAIRE_GENERIQUE = (
    "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=600&auto=format"
)


def obtenir_url_photo(vehicule: Vehicule) -> str:
    """Retourne l'URL photo du vehicule (enregistree, catalogue ou generique)."""
    if vehicule.photo_url and vehicule.photo_url.strip():
        return vehicule.photo_url.strip()

    marque = vehicule.marque.lower().strip()
    modele = vehicule.modele.lower().strip()
    cle = (marque, modele)
    if cle in IMAGES_PAR_MODELE:
        return IMAGES_PAR_MODELE[cle]

    for (m, mod), url in IMAGES_PAR_MODELE.items():
        if m in modele or mod in modele or m in marque:
            return url

    return IMAGE_UTILITAIRE_GENERIQUE
