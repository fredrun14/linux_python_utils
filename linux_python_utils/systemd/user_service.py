"""Implémentation Linux de la gestion des unités service utilisateur."""

import os

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    UserServiceUnitManager,
    ServiceConfig
)
from linux_python_utils.systemd.executor import UserSystemdExecutor
from linux_python_utils.systemd.validators import validate_service_name


class LinuxUserServiceUnitManager(UserServiceUnitManager):
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

    def generate_service_unit(self, config: ServiceConfig) -> str:
        """
        Génère le contenu d'un fichier .service systemd.

        Args:
            config: Configuration du service

        Returns:
            Contenu du fichier .service
        """
        lines = [
            "[Unit]",
            f"Description={config.description}",
            "",
            "[Service]",
            f"Type={config.type}",
            f"ExecStart={config.exec_start}"
        ]

        # Note: User et Group sont généralement omis pour les unités
        # utilisateur car elles s'exécutent déjà en tant qu'utilisateur
        if config.working_directory:
            lines.append(f"WorkingDirectory={config.working_directory}")

        # Variables d'environnement
        for key, value in config.environment.items():
            lines.append(f"Environment={key}={value}")

        # Options de redémarrage
        if config.restart != "no":
            lines.append(f"Restart={config.restart}")
            if config.restart_sec > 0:
                lines.append(f"RestartSec={config.restart_sec}")

        lines.extend([
            "",
            "[Install]",
            f"WantedBy={config.wanted_by}"
        ])

        return "\n".join(lines) + "\n"

    def install_service_unit(self, config: ServiceConfig) -> bool:
        """
        Installe une unité .service utilisateur.

        Args:
            config: Configuration du service

        Returns:
            True si succès, False sinon
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

        # Générer et écrire le fichier .service
        service_content = self.generate_service_unit(config)
        if not self._write_unit_file(
            f"{service_name}.service",
            service_content
        ):
            return False

        # Recharger systemd utilisateur
        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Service utilisateur {service_name}.service installé"
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
        # Générer et écrire le fichier .service
        service_content = self.generate_service_unit(config)
        if not self._write_unit_file(
            f"{service_name}.service",
            service_content
        ):
            return False

        # Recharger systemd utilisateur
        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Service utilisateur {service_name}.service installé"
        )
        return True

    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service utilisateur.

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
        Arrête un service utilisateur.

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
        Redémarre un service utilisateur.

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
        Active un service utilisateur.

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
        Désactive un service utilisateur.

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
        Supprime un fichier .service utilisateur.

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

        # Recharger systemd utilisateur
        self.reload_systemd()
        self.logger.log_info(
            f"Service utilisateur {service_name}.service supprimé"
        )
        return True

    def get_service_status(self, service_name: str) -> str | None:
        """
        Récupère le statut d'un service utilisateur.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            Statut du service ou None si erreur
        """
        validate_service_name(service_name)
        return self.get_status(f"{service_name}.service")

    def is_service_active(self, service_name: str) -> bool:
        """
        Vérifie si un service utilisateur est actif.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si actif, False sinon
        """
        return self.get_service_status(service_name) == "active"

    def is_service_enabled(self, service_name: str) -> bool:
        """
        Vérifie si un service utilisateur est activé au démarrage.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si activé, False sinon
        """
        validate_service_name(service_name)
        return self.executor.is_enabled(f"{service_name}.service")
