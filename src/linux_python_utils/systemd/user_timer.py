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

    def generate_timer_unit(self, config: TimerConfig) -> str:
        """
        Génère le contenu d'un fichier .timer systemd.

        Args:
            config: Configuration du timer

        Returns:
            Contenu du fichier .timer
        """
        lines = [
            "[Unit]",
            f"Description={config.description}",
            "",
            "[Timer]",
            f"Unit={config.unit}"
        ]

        # Ajouter les options de planification
        if config.on_calendar:
            lines.append(f"OnCalendar={config.on_calendar}")
        if config.on_boot_sec:
            lines.append(f"OnBootSec={config.on_boot_sec}")
        if config.on_unit_active_sec:
            lines.append(f"OnUnitActiveSec={config.on_unit_active_sec}")
        if config.persistent:
            lines.append("Persistent=true")
        if config.randomized_delay_sec:
            lines.append(f"RandomizedDelaySec={config.randomized_delay_sec}")

        lines.extend([
            "",
            "[Install]",
            "WantedBy=timers.target"
        ])

        return "\n".join(lines) + "\n"

    def install_timer_unit(self, config: TimerConfig) -> bool:
        """
        Installe une unité .timer utilisateur.

        Args:
            config: Configuration du timer

        Returns:
            True si succès, False sinon
        """
        # Extraire le nom du timer depuis le nom de l'unité cible
        # Ex: "backup.service" → "backup"
        timer_name = config.unit.rsplit(".", 1)[0]

        # Générer et écrire le fichier .timer
        timer_content = self.generate_timer_unit(config)
        if not self._write_unit_file(f"{timer_name}.timer", timer_content):
            return False

        # Recharger systemd utilisateur
        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Timer utilisateur {timer_name}.timer installé pour {config.unit}"
        )
        return True
