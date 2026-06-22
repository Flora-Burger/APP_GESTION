"""Script d'initialisation de la base de donnees avec des donnees d'exemple."""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from sqlalchemy import func, select

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.modules.imprimantes.modeles import Imprimante, ImprimanteEvenement
from backend.app.modules.ordinateurs.modeles import Ordinateur, OrdinateurEvenement
from backend.app.modules.vehicules.modeles import Vehicule, VehiculeJournal


def creer_tables():
    """Cree les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)


def inserer_donnees_exemple():
    """Insere des vehicules et journaux de demonstration."""
    session = SessionLocal()

    try:
        nb_vehicules = session.scalar(select(func.count()).select_from(Vehicule))
        if nb_vehicules and nb_vehicules > 0:
            print("Des vehicules existent deja. Seed vehicules ignore.")
        else:
            _inserer_vehicules(session)
            session.commit()
            print("Donnees vehicules d'exemple inserees avec succes.")

        nb_imprimantes = session.scalar(select(func.count()).select_from(Imprimante))
        if nb_imprimantes and nb_imprimantes > 0:
            print("Des imprimantes existent deja. Seed imprimantes ignore.")
        else:
            _inserer_imprimantes(session)
            session.commit()
            print("Donnees imprimantes d'exemple inserees avec succes.")

        nb_ordinateurs = session.scalar(select(func.count()).select_from(Ordinateur))
        if nb_ordinateurs and nb_ordinateurs > 0:
            print("Des ordinateurs existent deja. Seed ordinateurs ignore.")
        else:
            _inserer_ordinateurs(session)
            session.commit()
            print("Donnees ordinateurs d'exemple inserees avec succes.")

    finally:
        session.close()


def _inserer_vehicules(session) -> None:
    """Insere les vehicules et leurs journaux."""
    aujourdhui = date.today()
    vehicules_data = [
        {
            "matricule": "1234-ABC",
            "marque": "Renault",
            "modele": "Kangoo",
            "photo_url": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400",
            "date_expiration_itv": aujourdhui + timedelta(days=180),
            "kilometrage_actuel": 45185,
            "consommation_moyenne": Decimal("6.50"),
        },
        {
            "matricule": "5678-DEF",
            "marque": "Peugeot",
            "modele": "Partner",
            "photo_url": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",
            "date_expiration_itv": aujourdhui + timedelta(days=20),
            "kilometrage_actuel": 78045,
            "consommation_moyenne": Decimal("7.20"),
        },
        {
            "matricule": "9012-GHI",
            "marque": "Ford",
            "modele": "Transit",
            "photo_url": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=400",
            "date_expiration_itv": aujourdhui - timedelta(days=10),
            "kilometrage_actuel": 120430,
            "consommation_moyenne": Decimal("9.80"),
        },
        {
            "matricule": "3456-JKL",
            "marque": "Citroen",
            "modele": "Berlingo",
            "photo_url": "",
            "date_expiration_itv": aujourdhui + timedelta(days=90),
            "kilometrage_actuel": 32000,
            "consommation_moyenne": Decimal("5.40"),
        },
        {
            "matricule": "7890-MNO",
            "marque": "Toyota",
            "modele": "Proace",
            "photo_url": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400",
            "date_expiration_itv": aujourdhui + timedelta(days=365),
            "kilometrage_actuel": 55142,
            "consommation_moyenne": Decimal("4.80"),
        },
    ]

    journaux_par_vehicule = [
        [
            {
                "offset": 0,
                "utilisateur": "Carlos Mendez",
                "km_jour": 85,
                "conso": Decimal("5.20"),
                "cout": Decimal("8.50"),
            },
            {
                "offset": 1,
                "utilisateur": "Carlos Mendez",
                "km_jour": 120,
                "conso": Decimal("7.50"),
                "cout": Decimal("12.00"),
            },
        ],
        [
            {
                "offset": 0,
                "utilisateur": "Ana Ruiz",
                "km_jour": 45,
                "conso": Decimal("3.80"),
                "cout": Decimal("6.20"),
            },
            {
                "offset": 1,
                "utilisateur": None,
                "km_jour": 0,
                "conso": Decimal("0.00"),
                "cout": Decimal("0.00"),
            },
        ],
        [
            {
                "offset": 0,
                "utilisateur": "Pedro Lopez",
                "km_jour": 250,
                "conso": Decimal("22.00"),
                "cout": Decimal("35.00"),
            },
            {
                "offset": 1,
                "utilisateur": "Pedro Lopez",
                "km_jour": 180,
                "conso": Decimal("16.50"),
                "cout": Decimal("26.40"),
            },
        ],
        [
            {
                "offset": 0,
                "utilisateur": None,
                "km_jour": 0,
                "conso": Decimal("0.00"),
                "cout": Decimal("0.00"),
            },
        ],
        [
            {
                "offset": 0,
                "utilisateur": "Maria Garcia",
                "km_jour": 35,
                "conso": Decimal("2.10"),
                "cout": Decimal("3.40"),
            },
            {
                "offset": 1,
                "utilisateur": "Maria Garcia",
                "km_jour": 42,
                "conso": Decimal("2.50"),
                "cout": Decimal("4.00"),
            },
        ],
    ]

    for i, data in enumerate(vehicules_data):
        vehicule = Vehicule(**data)
        session.add(vehicule)
        session.flush()

        km_cumul = data["kilometrage_actuel"] - sum(
            j["km_jour"] for j in journaux_par_vehicule[i]
        )

        for journal_data in sorted(
            journaux_par_vehicule[i], key=lambda j: j["offset"], reverse=True
        ):
            jour = aujourdhui - timedelta(days=journal_data["offset"])
            km_cumul += journal_data["km_jour"]
            journal = VehiculeJournal(
                vehicule_id=vehicule.id,
                date_jour=jour,
                utilisateur=journal_data["utilisateur"],
                kilometrage_actuel=km_cumul,
                kilometrage_jour=journal_data["km_jour"],
                consommation_jour=journal_data["conso"],
                cout_carburant_jour=journal_data["cout"],
            )
            session.add(journal)


def _inserer_imprimantes(session) -> None:
    """Insere des imprimantes fictives avec historique d'evenements."""
    aujourdhui = date.today()

    imprimantes_data = [
        {
            "nom": "IMP-RECEP",
            "modele": "HP LaserJet Pro M404dn",
            "localisation": "Recepcion",
            "statut": "ok",
            "compteur_pages": 45200,
            "date_dernier_toner": aujourdhui - timedelta(days=45),
            "date_derniere_maintenance": aujourdhui - timedelta(days=120),
            "evenements": [
                {
                    "offset": 365,
                    "type": "compteur",
                    "compteur": 38000,
                    "commentaire": "Instalacion",
                },
                {
                    "offset": 120,
                    "type": "maintenance",
                    "compteur": 41000,
                    "commentaire": "Revision anual",
                },
                {
                    "offset": 119,
                    "type": "maintenance_terminee",
                    "compteur": 41000,
                    "commentaire": "Revision completada",
                },
                {
                    "offset": 45,
                    "type": "toner",
                    "compteur": 43500,
                    "commentaire": "Toner negro sustituido",
                },
                {
                    "offset": 5,
                    "type": "compteur",
                    "compteur": 45200,
                    "commentaire": "Lectura mensual",
                },
            ],
        },
        {
            "nom": "IMP-ADMIN",
            "modele": "Canon imageRUNNER 2630i",
            "localisation": "Administracion",
            "statut": "ok",
            "compteur_pages": 128500,
            "date_dernier_toner": aujourdhui - timedelta(days=30),
            "date_derniere_maintenance": aujourdhui - timedelta(days=90),
            "evenements": [
                {
                    "offset": 500,
                    "type": "compteur",
                    "compteur": 95000,
                    "commentaire": "Instalacion",
                },
                {
                    "offset": 90,
                    "type": "maintenance",
                    "compteur": 122000,
                    "commentaire": "Limpieza interna",
                },
                {
                    "offset": 89,
                    "type": "maintenance_terminee",
                    "compteur": 122000,
                    "commentaire": "Limpieza completada",
                },
                {
                    "offset": 30,
                    "type": "toner",
                    "compteur": 126800,
                    "commentaire": "Kit toner CMYK",
                },
                {
                    "offset": 2,
                    "type": "compteur",
                    "compteur": 128500,
                    "commentaire": None,
                },
            ],
        },
        {
            "nom": "IMP-ALM",
            "modele": "Brother HL-L2350DW",
            "localisation": "Almacen",
            "statut": "panne",
            "compteur_pages": 89300,
            "date_dernier_toner": aujourdhui - timedelta(days=60),
            "date_derniere_maintenance": aujourdhui - timedelta(days=200),
            "evenements": [
                {
                    "offset": 400,
                    "type": "compteur",
                    "compteur": 65000,
                    "commentaire": "Instalacion",
                },
                {
                    "offset": 60,
                    "type": "toner",
                    "compteur": 87000,
                    "commentaire": None,
                },
                {
                    "offset": 7,
                    "type": "panne",
                    "compteur": 89300,
                    "commentaire": "Atasco frecuente en bandeja",
                },
            ],
        },
        {
            "nom": "IMP-SALA",
            "modele": "Epson WorkForce Pro WF-4830",
            "localisation": "Sala de reuniones",
            "statut": "maintenance",
            "compteur_pages": 22100,
            "date_dernier_toner": aujourdhui - timedelta(days=15),
            "date_derniere_maintenance": aujourdhui - timedelta(days=3),
            "evenements": [
                {
                    "offset": 200,
                    "type": "compteur",
                    "compteur": 15000,
                    "commentaire": "Instalacion",
                },
                {
                    "offset": 15,
                    "type": "toner",
                    "compteur": 21500,
                    "commentaire": None,
                },
                {
                    "offset": 3,
                    "type": "maintenance",
                    "compteur": 22100,
                    "commentaire": "En taller tecnico",
                },
            ],
        },
        {
            "nom": "IMP-TALLER",
            "modele": "HP LaserJet MFP M234sdw",
            "localisation": "Taller",
            "statut": "ok",
            "compteur_pages": 67500,
            "date_dernier_toner": aujourdhui - timedelta(days=20),
            "date_derniere_maintenance": aujourdhui - timedelta(days=45),
            "evenements": [
                {
                    "offset": 300,
                    "type": "compteur",
                    "compteur": 50000,
                    "commentaire": "Instalacion",
                },
                {
                    "offset": 45,
                    "type": "maintenance",
                    "compteur": 64000,
                    "commentaire": "Rodillos de arrastre",
                },
                {
                    "offset": 20,
                    "type": "toner",
                    "compteur": 66200,
                    "commentaire": None,
                },
                {
                    "offset": 10,
                    "type": "reparation",
                    "compteur": 67000,
                    "commentaire": "Sensor de papel sustituido",
                },
                {
                    "offset": 3,
                    "type": "maintenance_terminee",
                    "compteur": 67200,
                    "commentaire": "Intervencion finalizada",
                },
                {
                    "offset": 1,
                    "type": "compteur",
                    "compteur": 67500,
                    "commentaire": None,
                },
            ],
        },
    ]

    for data in imprimantes_data:
        evenements = data.pop("evenements")
        imprimante = Imprimante(**data)
        session.add(imprimante)
        session.flush()

        for evt in evenements:
            session.add(
                ImprimanteEvenement(
                    imprimante_id=imprimante.id,
                    date_evenement=aujourdhui - timedelta(days=evt["offset"]),
                    type_evenement=evt["type"],
                    compteur_pages=evt["compteur"],
                    commentaire=evt["commentaire"],
                )
            )


def _inserer_ordinateurs(session) -> None:
    """Insere des ordinateurs fictifs avec historique d'evenements."""
    aujourdhui = date.today()

    ordinateurs_data = [
        {
            "nom": "PC-RECEP",
            "numero_serie": "DL-SN-2021-001",
            "marque": "Dell",
            "modele": "OptiPlex 7090",
            "utilisateur_assigne": "Maria Lopez",
            "localisation": "Recepcion",
            "statut": "ok",
            "systeme_exploitation": "Windows 11 Pro",
            "processeur": "Intel Core i5-11500",
            "memoire_ram": "16 Go",
            "capacite_stockage": "512 Go SSD",
            "date_acquisition": aujourdhui - timedelta(days=900),
            "garantie": "Hasta 03/2025",
            "evenements": [
                {
                    "offset": 900,
                    "type": "changement_utilisateur",
                    "responsable": "Maria Lopez",
                    "commentaire": "Puesto de recepcion",
                },
                {
                    "offset": 120,
                    "type": "entretien",
                    "responsable": "Soporte IT",
                    "commentaire": "Revision anual",
                },
                {
                    "offset": 119,
                    "type": "maintenance_terminee",
                    "responsable": "Soporte IT",
                    "commentaire": "Revision completada",
                },
            ],
        },
        {
            "nom": "PC-ADMIN",
            "numero_serie": "HP-SN-2022-014",
            "marque": "HP",
            "modele": "EliteDesk 800 G8",
            "utilisateur_assigne": "Carlos Ruiz",
            "localisation": "Administracion",
            "statut": "ok",
            "systeme_exploitation": "Windows 11 Pro",
            "processeur": "Intel Core i7-11700",
            "memoire_ram": "32 Go",
            "capacite_stockage": "1 To SSD",
            "date_acquisition": aujourdhui - timedelta(days=600),
            "garantie": "Hasta 09/2026",
            "evenements": [
                {
                    "offset": 600,
                    "type": "changement_utilisateur",
                    "responsable": "Carlos Ruiz",
                    "commentaire": "Responsable administracion",
                },
                {
                    "offset": 30,
                    "type": "entretien",
                    "responsable": "Soporte IT",
                    "commentaire": "Revision preventiva",
                },
            ],
        },
        {
            "nom": "PC-ALM",
            "numero_serie": "LN-SN-2019-088",
            "marque": "Lenovo",
            "modele": "ThinkCentre M720q",
            "utilisateur_assigne": None,
            "localisation": "Almacen",
            "statut": "en_panne",
            "systeme_exploitation": "Windows 10 Pro",
            "processeur": "Intel Core i3-9100T",
            "memoire_ram": "8 Go",
            "capacite_stockage": "256 Go SSD",
            "date_acquisition": aujourdhui - timedelta(days=1500),
            "garantie": None,
            "evenements": [
                {
                    "offset": 400,
                    "type": "changement_utilisateur",
                    "responsable": "Pedro Gomez",
                    "commentaire": "Terminal almacen",
                },
                {
                    "offset": 60,
                    "type": "changement_utilisateur",
                    "responsable": None,
                    "commentaire": "Equipo retirado del puesto",
                },
                {
                    "offset": 10,
                    "type": "panne",
                    "responsable": "Soporte IT",
                    "commentaire": "No arranca tras corte de luz",
                },
            ],
        },
        {
            "nom": "PC-TALLER",
            "numero_serie": "DL-SN-2020-045",
            "marque": "Dell",
            "modele": "Precision 3650",
            "utilisateur_assigne": "Ana Torres",
            "localisation": "Taller",
            "statut": "en_maintenance",
            "systeme_exploitation": "Windows 11 Pro",
            "processeur": "Intel Core i7-11700",
            "memoire_ram": "32 Go",
            "capacite_stockage": "2 To HDD + 512 Go SSD",
            "date_acquisition": aujourdhui - timedelta(days=1100),
            "garantie": "Hasta 12/2025",
            "evenements": [
                {
                    "offset": 1100,
                    "type": "changement_utilisateur",
                    "responsable": "Ana Torres",
                    "commentaire": "Estacion CAD",
                },
                {
                    "offset": 5,
                    "type": "entretien",
                    "responsable": "Soporte IT",
                    "commentaire": "Sustitucion fuente de alimentacion",
                },
            ],
        },
        {
            "nom": "PC-SALA",
            "numero_serie": "AP-SN-2023-002",
            "marque": "Apple",
            "modele": "iMac 24",
            "utilisateur_assigne": None,
            "localisation": "Sala de reuniones",
            "statut": "ok",
            "systeme_exploitation": "macOS Sonoma",
            "processeur": "Apple M3",
            "memoire_ram": "16 Go",
            "capacite_stockage": "512 Go SSD",
            "date_acquisition": aujourdhui - timedelta(days=300),
            "garantie": "AppleCare hasta 2026",
            "evenements": [
                {
                    "offset": 90,
                    "type": "entretien",
                    "responsable": "Soporte IT",
                    "commentaire": "Preparacion sala reuniones",
                },
                {
                    "offset": 89,
                    "type": "intervention_technique",
                    "responsable": "Soporte IT",
                    "commentaire": "Listo para videoconferencias",
                },
            ],
        },
        {
            "nom": "PORT-JEFE",
            "numero_serie": "LN-SN-2024-011",
            "marque": "Lenovo",
            "modele": "ThinkPad X1 Carbon",
            "utilisateur_assigne": "Director General",
            "localisation": "Direccion",
            "statut": "ok",
            "systeme_exploitation": "Windows 11 Pro",
            "processeur": "Intel Core i7-1365U",
            "memoire_ram": "16 Go",
            "capacite_stockage": "1 To SSD",
            "date_acquisition": aujourdhui - timedelta(days=180),
            "garantie": "On-site 3 anos",
            "evenements": [
                {
                    "offset": 180,
                    "type": "changement_utilisateur",
                    "responsable": "Director General",
                    "commentaire": "Portatil direccion",
                },
                {
                    "offset": 45,
                    "type": "intervention_technique",
                    "responsable": "Soporte IT",
                    "commentaire": "Optimizacion rendimiento",
                },
            ],
        },
    ]

    for data in ordinateurs_data:
        evenements = data.pop("evenements")
        ordinateur = Ordinateur(**data)
        session.add(ordinateur)
        session.flush()

        for evt in evenements:
            session.add(
                OrdinateurEvenement(
                    ordinateur_id=ordinateur.id,
                    date_evenement=aujourdhui - timedelta(days=evt["offset"]),
                    type_evenement=evt["type"],
                    commentaire=evt.get("commentaire"),
                    utilisateur_responsable=evt.get("responsable"),
                )
            )


if __name__ == "__main__":
    creer_tables()
    inserer_donnees_exemple()
