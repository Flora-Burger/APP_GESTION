"""Modeles SQLAlchemy pour le module vehicules."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Vehicule(Base):
    """Vehicule de fonction - donnees maitres."""

    __tablename__ = "vehicules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    matricule: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    marque: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    modele: Mapped[str] = mapped_column(String(100), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    date_expiration_itv: Mapped[date] = mapped_column(Date, nullable=False)
    kilometrage_actuel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consommation_moyenne: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("0.00")
    )
    utilisateur_assigne: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seguro_compania: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seguro_poliza: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seguro_tel_asistencia: Mapped[str | None] = mapped_column(String(30), nullable=True)
    seguro_tel_grua: Mapped[str | None] = mapped_column(String(30), nullable=True)
    seguro_tel_emergencias: Mapped[str | None] = mapped_column(String(30), nullable=True)
    seguro_otro_contacto: Mapped[str | None] = mapped_column(String(30), nullable=True)
    talleres_referencia: Mapped[str | None] = mapped_column(Text, nullable=True)

    journaux: Mapped[list["VehiculeJournal"]] = relationship(
        "VehiculeJournal",
        back_populates="vehicule",
        cascade="all, delete-orphan",
        order_by="desc(VehiculeJournal.date_jour)",
    )
    immobilisations: Mapped[list["VehiculeImmobilisation"]] = relationship(
        "VehiculeImmobilisation",
        back_populates="vehicule",
        cascade="all, delete-orphan",
        order_by="desc(VehiculeImmobilisation.date_debut)",
    )


class VehiculeImmobilisation(Base):
    """Immobilisation d'un vehicule au garage."""

    __tablename__ = "vehicule_immobilisations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicules.id", ondelete="CASCADE"), nullable=False
    )
    motif: Mapped[str] = mapped_column(String(30), nullable=False)
    garage: Mapped[str] = mapped_column(String(200), nullable=False)
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)
    date_retour_estimee: Mapped[date | None] = mapped_column(Date, nullable=True)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_fin: Mapped[date | None] = mapped_column(Date, nullable=True)

    vehicule: Mapped["Vehicule"] = relationship("Vehicule", back_populates="immobilisations")


class VehiculeJournal(Base):
    """Historique quotidien d'un vehicule."""

    __tablename__ = "vehicule_journaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicules.id", ondelete="CASCADE"), nullable=False
    )
    date_jour: Mapped[date] = mapped_column(Date, nullable=False)
    utilisateur: Mapped[str | None] = mapped_column(String(200), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kilometrage_actuel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kilometrage_jour: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consommation_jour: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=Decimal("0.00")
    )
    cout_carburant_jour: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=Decimal("0.00")
    )

    vehicule: Mapped["Vehicule"] = relationship("Vehicule", back_populates="journaux")
