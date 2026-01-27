"""Implémentation Linux de la gestion des services systemd."""

import subprocess
from typing import List, Optional

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import SystemdServiceManager


class LinuxSystemdServiceManager(SystemdServiceManager):
    """
    Implémentation Linux de la gestion des services systemd.

    Utilise subprocess pour exécuter les commandes systemctl.
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialise le gestionnaire de services.

        Args:
            logger: Instance de Logger pour le logging
        """
        self.logger = logger

    def _run_systemctl(
        self,
        args: List[str],
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Exécute une commande systemctl.

        Args:
            args: Arguments de la commande systemctl
            check: Lever une exception si la commande échoue

        Returns:
            Résultat de la commande
        """
        cmd = ["systemctl"] + args
        return subprocess.run(cmd, check=check, capture_output=True, text=True)

    def enable_timer(self, timer_name: str) -> bool:
        """
        Active et démarre un timer systemd.

        Args:
            timer_name: Nom du timer

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["enable", "--now", timer_name])
            self.logger.log_info(
                f"Timer {timer_name} activé et démarré avec succès."
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors de l'activation du timer {timer_name}: {e}"
            )
            return False

    def disable_timer(self, timer_name: str) -> bool:
        """
        Désactive et arrête un timer systemd.

        Args:
            timer_name: Nom du timer

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["disable", "--now", timer_name])
            self.logger.log_info(
                f"Timer {timer_name} désactivé et arrêté."
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors de la désactivation du timer {timer_name}: {e}"
            )
            return False

    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd.

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["daemon-reload"])
            self.logger.log_info("Systemd rechargé avec succès.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors du rechargement de systemd: {e}"
            )
            return False

    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service systemd.

        Args:
            service_name: Nom du service

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["start", service_name])
            self.logger.log_info(f"Service {service_name} démarré.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors du démarrage de {service_name}: {e}"
            )
            return False

    def stop_service(self, service_name: str) -> bool:
        """
        Arrête un service systemd.

        Args:
            service_name: Nom du service

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["stop", service_name])
            self.logger.log_info(f"Service {service_name} arrêté.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors de l'arrêt de {service_name}: {e}"
            )
            return False

    def get_status(self, unit_name: str) -> Optional[str]:
        """
        Récupère le statut d'une unité systemd.

        Args:
            unit_name: Nom de l'unité (service ou timer)

        Returns:
            Statut de l'unité ou None si erreur
        """
        try:
            result = self._run_systemctl(
                ["is-active", unit_name],
                check=False
            )
            return result.stdout.strip()
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la récupération du statut de {unit_name}: {e}"
            )
            return None

    def is_active(self, unit_name: str) -> bool:
        """
        Vérifie si une unité systemd est active.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si active, False sinon
        """
        return self.get_status(unit_name) == "active"
