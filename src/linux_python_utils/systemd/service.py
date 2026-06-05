"""Implémentation Linux de la gestion des unités service systemd."""

import os
import shlex

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    _ServiceOperationsMixin,
    ServiceUnitManager,
    ServiceConfig,
)
from linux_python_utils.systemd.executor import SystemdExecutor
from linux_python_utils.systemd.validators import validate_service_name


class LinuxServiceUnitManager(_ServiceOperationsMixin, ServiceUnitManager):
    """Implémentation Linux de la gestion des unités .service systemd.

    Génère et installe des fichiers unit systemd pour les services
    (démons, scripts de démarrage, etc.).

    Attributes:
        logger: Instance de Logger pour le logging.
        executor: Instance de SystemdExecutor pour les opérations systemctl.
        SYSTEMD_UNIT_PATH: Chemin du répertoire des unités systemd.
    """

    def __init__(
        self,
        logger: Logger,
        executor: SystemdExecutor
    ) -> None:
        """
        Initialise le gestionnaire d'unités service.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de SystemdExecutor pour les opérations systemctl
        """
        super().__init__(logger, executor)

    def install_service_unit(self, config: ServiceConfig) -> bool:
        """Installe une unité .service.

        Args:
            config: Configuration du service.

        Returns:
            True si succès, False sinon.
        """
        # Extraire le nom du service depuis exec_start
        service_name = os.path.basename(
            shlex.split(config.exec_start)[0]
        ).replace(".", "-")
        try:
            validate_service_name(service_name)
        except ValueError as e:
            self.logger.log_error(
                f"Nom de service invalide : {e}"
            )
            return False

        service_file = f"{service_name}.service"
        service_content = config.to_unit_file()

        if not self._write_unit_file(service_file, service_content):
            return False

        if not self.reload_systemd():
            return False

        self.logger.log_info(f"Service {service_file} installé")
        return True

    def install_service_unit_with_name(
        self,
        service_name: str,
        config: ServiceConfig
    ) -> bool:
        """Installe une unité .service avec un nom spécifique.

        Args:
            service_name: Nom du service (sans extension).
            config: Configuration du service.

        Returns:
            True si succès, False sinon.
        """
        try:
            validate_service_name(service_name)
        except ValueError as e:
            self.logger.log_error(
                f"Nom de service invalide : {e}"
            )
            return False
        service_file = f"{service_name}.service"
        service_content = config.to_unit_file()

        if not self._write_unit_file(service_file, service_content):
            return False

        if not self.reload_systemd():
            return False

        self.logger.log_info(f"Service {service_file} installé")
        return True
