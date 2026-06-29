"""Acces base pour la configuration globale vehicules."""

from sqlalchemy.orm import Session

from backend.app.modules.vehicules.configuration_modeles import VehiculesConfiguration


class ConfigurationVehiculesRepository:
    """Lecture/ecriture de la ligne de configuration unique."""

    def __init__(self, session: Session):
        self.session = session

    def obtenir(self) -> VehiculesConfiguration:
        config = self.session.get(VehiculesConfiguration, 1)
        if config is None:
            config = VehiculesConfiguration(id=1)
            self.session.add(config)
            self.session.commit()
            self.session.refresh(config)
        return config

    def sauvegarder(self, config: VehiculesConfiguration) -> VehiculesConfiguration:
        self.session.add(config)
        self.session.commit()
        self.session.refresh(config)
        return config
