"""Modeles SQLAlchemy pour le module ordinateurs."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Ordinateur(Base):
    """Ordinateur du parc informatique - donnees maitres."""

    __tablename__ = "ordinateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    numero_serie: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    marque: Mapped[str] = mapped_column(String(100), nullable=False)
    modele: Mapped[str] = mapped_column(String(150), nullable=False)
    utilisateur_assigne: Mapped[str | None] = mapped_column(String(150), nullable=True)
    localisation: Mapped[str] = mapped_column(String(200), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    statut: Mapped[str] = mapped_column(String(30), nullable=False, default="ok")
    systeme_exploitation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processeur: Mapped[str | None] = mapped_column(String(150), nullable=True)
    memoire_ram: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacite_stockage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_acquisition: Mapped[date | None] = mapped_column(Date, nullable=True)
    garantie: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    evenements: Mapped[list["OrdinateurEvenement"]] = relationship(
        "OrdinateurEvenement",
        back_populates="ordinateur",
        cascade="all, delete-orphan",
        order_by="desc(OrdinateurEvenement.date_evenement)",
    )


class OrdinateurEvenement(Base):
    """Historique des evenements d'un ordinateur."""

    __tablename__ = "ordinateur_evenements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ordinateur_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ordinateurs.id", ondelete="CASCADE"), nullable=False
    )
    date_evenement: Mapped[date] = mapped_column(Date, nullable=False)
    type_evenement: Mapped[str] = mapped_column(String(40), nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    utilisateur_responsable: Mapped[str | None] = mapped_column(String(150), nullable=True)

    ordinateur: Mapped["Ordinateur"] = relationship("Ordinateur", back_populates="evenements")
