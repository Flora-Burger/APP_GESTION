"""Configuration de la base de donnees SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from backend.app.core.config import RACINE_PROJET, obtenir_parametres

parametres = obtenir_parametres()

if parametres.database_url.startswith("sqlite"):
    (RACINE_PROJET / "data").mkdir(parents=True, exist_ok=True)

connect_args: dict = {}
engine_kwargs: dict = {}

if parametres.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif parametres.est_vercel():
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(
    parametres.database_url,
    connect_args=connect_args,
    echo=parametres.debug,
    pool_pre_ping=not parametres.database_url.startswith("sqlite"),
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe de base pour tous les modeles ORM."""


def obtenir_session() -> Generator[Session, None, None]:
    """Fournit une session de base de donnees (dependency injection)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
