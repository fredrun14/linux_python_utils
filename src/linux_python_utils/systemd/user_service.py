"""Implémentation Linux de la gestion des unités service utilisateur."""

import os
import shlex

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    _ServiceOperationsMixin,
    UserServiceUnitManager,
    ServiceConfig,
)
from linux_python_utils.systemd.executor import UserSystemdExecutor
from linux_python_utils.systemd.validators import validate_service_name


class LinuxUserServiceUnitManager(
    _ServiceOperationsMixin, UserServiceUnitManager
):
    """Implémentation Linux de la gestion des unités .service utilisateur.

    Génère et installe des fichiers unit systemd pour les services
    utilisateur (scripts, applications de fond, etc.).

    Les unités sont stockées dans ~/.config/systemd/user/ et ne
    nécessitent pas de privilèges root.

    Attributes:
        logger: Instance de Logger pour le logging.
        executor: Instance de UserSystemdExecutor pour les opérations.
        SYSTEMD_USER_UNIT_PATH: Chemin du répertoire des unités utilisateur.
    """

    _service_label = "Service utilisateur"

    def __init__(
        self,
        logger: Logger,
        executor: UserSystemdExecutor
    ) -> None:
        """
        Initialise le gestionnaire d'unités service utilisateur.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de UserSystemdExecutor pour les opérations
        """
        super().__init__(logger, executor)

    def install_service_unit(self, config: ServiceConfig) -> bool:
        """
        Installe une unité .service utilisateur.

        Args:
            config: Configuration du service

        Returns:
            True si succès, False sinon

        Raises:
            ValueError: Si un champ de config contient un caractère de contrôle.
        """
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

        self.logger.log_info(
            f"Service utilisateur {service_file} installé"
        )
        return True

    def install_service_unit_with_name(
        self,
        service_name: str,
        config: ServiceConfig
    ) -> bool:
        """
        Installe une unité .service utilisateur avec un nom spécifique.

        Args:
            service_name: Nom du service (sans extension)
            config: Configuration du service

        Returns:
            True si succès, False sinon
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

        self.logger.log_info(
            f"Service utilisateur {service_file} installé"
        )
        return True
