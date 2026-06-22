"""Configuration Alembic pour les migrations."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import obtenir_parametres
from backend.app.core.database import Base

# Importer tous les modeles pour que Alembic les detecte
from backend.app.modules.auth import modeles as modeles_auth  # noqa: F401
from backend.app.modules.imprimantes import modeles as modeles_imprimantes  # noqa: F401
from backend.app.modules.ordinateurs import modeles as modeles_ordinateurs  # noqa: F401
from backend.app.modules.vehicules import modeles as modeles_vehicules  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

parametres = obtenir_parametres()
config.set_main_option("sqlalchemy.url", parametres.database_url)


def run_migrations_offline() -> None:
    """Executer les migrations en mode offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executer les migrations en mode online."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
