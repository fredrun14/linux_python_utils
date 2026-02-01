"""Implémentation Linux de la gestion des unités service systemd."""

import os

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import ServiceUnitManager, ServiceConfig
from linux_python_utils.systemd.executor import SystemdExecutor


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

        # Ajouter les options optionnelles
        if config.user:
            lines.append(f"User={config.user}")
        if config.group:
            lines.append(f"Group={config.group}")
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

    def _write_unit_file(self, unit_name: str, content: str) -> bool:
        """
        Écrit un fichier unit dans le répertoire systemd.

        Args:
            unit_name: Nom du fichier (avec extension)
            content: Contenu du fichier

        Returns:
            True si succès, False sinon
        """
        unit_path = os.path.join(self.SYSTEMD_UNIT_PATH, unit_name)
        try:
            with open(unit_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.log_info(f"Fichier unit créé: {unit_path}")
            return True
        except PermissionError:
            self.logger.log_error(
                f"Permission refusée pour écrire {unit_path}. "
                "Exécution en tant que root requise."
            )
            return False
        except OSError as e:
            self.logger.log_error(
                f"Erreur lors de l'écriture de {unit_path}: {e}"
            )
            return False

    def _remove_unit_file(self, unit_name: str) -> bool:
        """
        Supprime un fichier unit du répertoire systemd.

        Args:
            unit_name: Nom du fichier (avec extension)

        Returns:
            True si succès ou fichier inexistant, False si erreur
        """
        unit_path = os.path.join(self.SYSTEMD_UNIT_PATH, unit_name)
        try:
            if os.path.exists(unit_path):
                os.remove(unit_path)
                self.logger.log_info(f"Fichier unit supprimé: {unit_path}")
            return True
        except PermissionError:
            self.logger.log_error(
                f"Permission refusée pour supprimer {unit_path}. "
                "Exécution en tant que root requise."
            )
            return False
        except OSError as e:
            self.logger.log_error(
                f"Erreur lors de la suppression de {unit_path}: {e}"
            )
            return False

    def install_service_unit(self, config: ServiceConfig) -> bool:
        """
        Installe une unité .service.

        Args:
            config: Configuration du service

        Returns:
            True si succès, False sinon
        """
        # Extraire le nom du service depuis la description ou générer un nom
        # On utilise le premier mot de exec_start comme base
        service_name = os.path.basename(
            config.exec_start.split()[0]
        ).replace(".", "-")

        # Générer et écrire le fichier .service
        service_content = self.generate_service_unit(config)
        if not self._write_unit_file(
            f"{service_name}.service",
            service_content
        ):
            return False

        # Recharger systemd
        if not self.reload_systemd():
            return False

        self.logger.log_info(f"Service {service_name}.service installé")
        return True

    def install_service_unit_with_name(
        self,
        service_name: str,
        config: ServiceConfig
    ) -> bool:
        """
        Installe une unité .service avec un nom spécifique.

        Args:
            service_name: Nom du service (sans extension)
            config: Configuration du service

        Returns:
            True si succès, False sinon
        """
        # Générer et écrire le fichier .service
        service_content = self.generate_service_unit(config)
        if not self._write_unit_file(
            f"{service_name}.service",
            service_content
        ):
            return False

        # Recharger systemd
        if not self.reload_systemd():
            return False

        self.logger.log_info(f"Service {service_name}.service installé")
        return True

    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
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
        # D'abord désactiver et arrêter le service
        self.disable_service(service_name)

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
        return self.executor.is_enabled(f"{service_name}.service")
