"""Images par defaut pour les ordinateurs sans photo."""

from backend.app.modules.ordinateurs.modeles import Ordinateur

URL_GENERIQUE = (
    "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&auto=format"
)

URLS_PAR_MARQUE: dict[str, str] = {
    "dell": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format",
    "hp": "https://images.unsplash.com/photo-1525547719578-a2d4ac910d26?w=600&auto=format",
    "lenovo": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format",
    "apple": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format",
}


def obtenir_url_photo(ordinateur: Ordinateur) -> str:
    """Retourne l'URL photo de l'ordinateur (enregistree ou generique)."""
    if ordinateur.photo_url and ordinateur.photo_url.strip():
        return ordinateur.photo_url.strip()

    marque = (ordinateur.marque or "").lower()
    for cle, url in URLS_PAR_MARQUE.items():
        if cle in marque:
            return url
    return URL_GENERIQUE
