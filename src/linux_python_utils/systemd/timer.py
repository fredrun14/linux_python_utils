"""Implémentation Linux de la gestion des unités timer systemd."""

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    _TimerOperationsMixin,
    TimerUnitManager,
    TimerConfig,
)
from linux_python_utils.systemd.executor import SystemdExecutor


class LinuxTimerUnitManager(_TimerOperationsMixin, TimerUnitManager):
    """Implémentation Linux de la gestion des unités .timer systemd.

    Génère et installe des fichiers unit systemd pour la planification
    de tâches récurrentes ou ponctuelles.

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
        Initialise le gestionnaire d'unités timer.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de SystemdExecutor pour les opérations systemctl
        """
        super().__init__(logger, executor)

    def install_timer_unit(self, config: TimerConfig) -> bool:
        """Installe une unité .timer.

        Args:
            config: Configuration du timer.

        Returns:
            True si succès, False sinon.
        """
        timer_file = f"{config.timer_name}.timer"
        timer_content = config.to_unit_file()

        if not self._write_unit_file(timer_file, timer_content):
            return False

        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Timer {timer_file} installé pour {config.unit}"
        )
        return True
