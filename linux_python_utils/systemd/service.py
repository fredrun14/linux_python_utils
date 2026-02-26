"""Implémentation Linux de la gestion des unités service systemd."""

import os

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import ServiceUnitManager, ServiceConfig
from linux_python_utils.systemd.executor import SystemdExecutor
from linux_python_utils.systemd.validators import validate_service_name


class LinuxServiceUnitManager(ServiceUnitManager):
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
            config.exec_start.split()[0]
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

    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        unit = f"{service_name}.service"
        return self.executor.start_unit(unit)

    def stop_service(self, service_name: str) -> bool:
        """
        Arrête un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        unit = f"{service_name}.service"
        return self.executor.stop_unit(unit)

    def restart_service(self, service_name: str) -> bool:
        """
        Redémarre un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        unit = f"{service_name}.service"
        return self.executor.restart_unit(unit)

    def enable_service(self, service_name: str) -> bool:
        """
        Active un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        unit = f"{service_name}.service"
        return self.enable(unit)

    def disable_service(self, service_name: str) -> bool:
        """
        Désactive un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        unit = f"{service_name}.service"
        return self.disable(unit)

    def remove_service_unit(self, service_name: str) -> bool:
        """
        Supprime un fichier .service.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si succès, False sinon
        """
        validate_service_name(service_name)
        # D'abord désactiver et arrêter le service
        if not self.disable_service(service_name):
            self.logger.log_warning(
                f"disable_service échoué pour {service_name!r} "
                "(service peut-être déjà inactif) — "
                "suppression du fichier unit quand même"
            )

        # Supprimer le fichier
        if not self._remove_unit_file(f"{service_name}.service"):
            return False

        # Recharger systemd
        self.reload_systemd()
        self.logger.log_info(f"Service {service_name}.service supprimé")
        return True

    def get_service_status(self, service_name: str) -> str | None:
        """
        Récupère le statut d'un service.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            Statut du service ou None si erreur
        """
        validate_service_name(service_name)
        return self.get_status(f"{service_name}.service")

    def is_service_active(self, service_name: str) -> bool:
        """
        Vérifie si un service est actif.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si actif, False sinon
        """
        return self.get_service_status(service_name) == "active"

    def is_service_enabled(self, service_name: str) -> bool:
        """
        Vérifie si un service est activé au démarrage.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si activé, False sinon
        """
        validate_service_name(service_name)
        return self.executor.is_enabled(f"{service_name}.service")
