"""Service pour la configuration globale seguro / talleres."""

from backend.app.modules.vehicules.configuration_repository import ConfigurationVehiculesRepository
from backend.app.modules.vehicules.donnees_json import (
    ContactoSeguro,
    TallerReferencia,
    parser_seguro_contactos,
    parser_talleres_referencia,
    serialiser_seguro_contactos,
    serialiser_talleres_referencia,
    talleres_tries_par_ciudad,
)
from backend.app.modules.vehicules.schemas import ConfigurationVehiculesResponse, ConfigurationVehiculesUpdate


class ConfigurationVehiculesService:
    """Gestion de la configuration partagee."""

    def __init__(self, session):
        self.repo = ConfigurationVehiculesRepository(session)

    def obtenir(self) -> ConfigurationVehiculesResponse:
        config = self.repo.obtenir()
        return ConfigurationVehiculesResponse(
            seguro_compania=config.seguro_compania,
            seguro_poliza=config.seguro_poliza,
            seguro_contactos=parser_seguro_contactos(config.seguro_contactos),
            talleres_referencia=talleres_tries_par_ciudad(
                parser_talleres_referencia(config.talleres_referencia)
            ),
        )

    def modifier(
        self,
        donnees: ConfigurationVehiculesUpdate,
        contactos: list[ContactoSeguro],
        talleres: list[TallerReferencia],
    ) -> ConfigurationVehiculesResponse:
        config = self.repo.obtenir()
        config.seguro_compania = (donnees.seguro_compania or "").strip() or None
        config.seguro_poliza = (donnees.seguro_poliza or "").strip() or None
        config.seguro_contactos = serialiser_seguro_contactos(contactos)
        config.talleres_referencia = serialiser_talleres_referencia(talleres)
        self.repo.sauvegarder(config)
        return self.obtenir()
