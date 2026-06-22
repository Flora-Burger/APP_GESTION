"""Modeles SQLAlchemy pour le module imprimantes."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Imprimante(Base):
    """Imprimante de l'entreprise - donnees maitres."""

    __tablename__ = "imprimantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    modele: Mapped[str] = mapped_column(String(150), nullable=False)
    localisation: Mapped[str] = mapped_column(String(200), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    compteur_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_dernier_toner: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_derniere_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    evenements: Mapped[list["ImprimanteEvenement"]] = relationship(
        "ImprimanteEvenement",
        back_populates="imprimante",
        cascade="all, delete-orphan",
        order_by="desc(ImprimanteEvenement.date_evenement)",
    )


class ImprimanteEvenement(Base):
    """Historique des evenements d'une imprimante."""

    __tablename__ = "imprimante_evenements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    imprimante_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("imprimantes.id", ondelete="CASCADE"), nullable=False
    )
    date_evenement: Mapped[date] = mapped_column(Date, nullable=False)
    type_evenement: Mapped[str] = mapped_column(String(20), nullable=False)
    compteur_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)

    imprimante: Mapped["Imprimante"] = relationship("Imprimante", back_populates="evenements")
