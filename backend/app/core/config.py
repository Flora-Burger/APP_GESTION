"""Configuration de l'application."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du projet (APP_GESTION)
RACINE_PROJET = Path(__file__).resolve().parents[3]


class Parametres(BaseSettings):
    """Parametres charges depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=RACINE_PROJET / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nom_entreprise: str = "FLORA"
    logo_url: str = "/static/img/logo.svg"
    database_url: str = (
        f"sqlite:///{(RACINE_PROJET / 'data' / 'flora.db').as_posix()}"
    )
    debug: bool = True
    jwt_secret: str = "changez-cette-cle-secrete-en-production-flora"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480
    cookie_auth_nom: str = "flora_token"
    cookie_secure: bool = False


@lru_cache
def obtenir_parametres() -> Parametres:
    """Retourne une instance cachee des parametres."""
    return Parametres()
