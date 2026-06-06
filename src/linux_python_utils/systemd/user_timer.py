"""Implémentation Linux de la gestion des unités timer utilisateur."""

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    _TimerOperationsMixin,
    UserTimerUnitManager,
    TimerConfig,
)
from linux_python_utils.systemd.executor import UserSystemdExecutor


class LinuxUserTimerUnitManager(_TimerOperationsMixin, UserTimerUnitManager):
    """Implémentation Linux de la gestion des unités .timer utilisateur.

    Génère et installe des fichiers unit systemd pour la planification
    de tâches récurrentes ou ponctuelles dans l'espace utilisateur.

    Les unités sont stockées dans ~/.config/systemd/user/ et ne
    nécessitent pas de privilèges root.

    Attributes:
        logger: Instance de Logger pour le logging.
        executor: Instance de UserSystemdExecutor pour les opérations.
        SYSTEMD_USER_UNIT_PATH: Chemin du répertoire des unités utilisateur.
    """

    _timer_label = "Timer utilisateur"

    def __init__(
        self,
        logger: Logger,
        executor: UserSystemdExecutor
    ) -> None:
        """
        Initialise le gestionnaire d'unités timer utilisateur.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de UserSystemdExecutor pour les opérations
        """
        super().__init__(logger, executor)

    def install_timer_unit(self, config: TimerConfig) -> bool:
        """
        Installe une unité .timer utilisateur.

        Args:
            config: Configuration du timer

        Returns:
            True si succès, False sinon

        Raises:
            ValueError: Si un champ de config contient un caractère de contrôle.
        """
        timer_file = f"{config.timer_name}.timer"
        timer_content = config.to_unit_file()

        if not self._write_unit_file(timer_file, timer_content):
            return False

        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Timer utilisateur {timer_file} installé pour {config.unit}"
        )
        return True
