"""Configuration de l'application."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du projet (APP_GESTION)
RACINE_PROJET = Path(__file__).resolve().parents[3]
FICHIER_ENV = RACINE_PROJET / ".env"


def normaliser_database_url(url: str) -> str:
    """Adapte l'URL pour SQLAlchemy (PostgreSQL via psycopg)."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def est_environnement_vercel() -> bool:
    """Indique si l'application tourne sur Vercel."""
    return os.getenv("VERCEL") == "1"


class Parametres(BaseSettings):
    """Parametres charges depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=FICHIER_ENV if FICHIER_ENV.is_file() else None,
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
    blob_read_write_token: str | None = None

    @model_validator(mode="after")
    def appliquer_regles_deploiement(self) -> Self:
        self.database_url = normaliser_database_url(self.database_url)
        if est_environnement_vercel():
            self.cookie_secure = True
            if self.database_url.startswith("sqlite"):
                msg = "DATABASE_URL PostgreSQL est requis sur Vercel."
                raise ValueError(msg)
        return self

    def utilise_blob(self) -> bool:
        """Indique si les uploads utilisent Vercel Blob."""
        return bool(self.blob_read_write_token)

    def est_vercel(self) -> bool:
        """Indique si l'application tourne sur Vercel."""
        return est_environnement_vercel()


@lru_cache
def obtenir_parametres() -> Parametres:
    """Retourne une instance cachee des parametres."""
    return Parametres()
