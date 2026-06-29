"""Configuration globale seguro y talleres (tous les vehicules)."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class VehiculesConfiguration(Base):
    """Parametres partages pour toute la flotte."""

    __tablename__ = "vehicules_configuration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    seguro_compania: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seguro_poliza: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seguro_contactos: Mapped[str | None] = mapped_column(Text, nullable=True)
    talleres_referencia: Mapped[str | None] = mapped_column(Text, nullable=True)
