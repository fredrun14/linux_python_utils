"""Implémentation Linux de la gestion des unités timer systemd."""

import json
import subprocess

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import TimerUnitManager, TimerConfig
from linux_python_utils.systemd.executor import SystemdExecutor
from linux_python_utils.systemd.validators import validate_unit_name


class LinuxTimerUnitManager(TimerUnitManager):
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

    def enable_timer(self, timer_name: str) -> bool:
        """
        Active un timer systemd.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(timer_name)
        unit = f"{timer_name}.timer"
        return self.enable(unit)

    def disable_timer(self, timer_name: str) -> bool:
        """
        Désactive un timer systemd.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(timer_name)
        unit = f"{timer_name}.timer"
        return self.disable(unit)

    def remove_timer_unit(self, timer_name: str) -> bool:
        """
        Supprime un fichier .timer.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(timer_name)
        # D'abord désactiver le timer
        self.disable_timer(timer_name)

        # Supprimer le fichier
        if not self._remove_unit_file(f"{timer_name}.timer"):
            return False

        # Recharger systemd
        self.reload_systemd()
        self.logger.log_info(f"Timer {timer_name}.timer supprimé")
        return True

    def get_timer_status(self, timer_name: str) -> str | None:
        """
        Récupère le statut d'un timer.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            Statut du timer ou None si erreur
        """
        validate_unit_name(timer_name)
        return self.get_status(f"{timer_name}.timer")

    def list_timers(self) -> list[dict[str, str]]:
        """Liste tous les timers actifs.

        Utilise ``--output=json`` pour un parsing fiable, avec
        fallback sur le parsing texte si le format JSON n'est pas
        supporté par la version de systemd installée.

        Returns:
            Liste de dictionnaires avec les infos des timers.

        Raises:
            RuntimeError: Si l'exécution de systemctl échoue.
        """
        try:
            result = subprocess.run(
                ["systemctl", "list-timers", "--no-pager",
                 "--output=json"],
                capture_output=True,
                text=True,
                check=False
            )
        except (FileNotFoundError, OSError) as e:
            raise RuntimeError(
                f"Impossible d'exécuter systemctl : {e}"
            ) from e

        if result.returncode != 0:
            # Fallback : --output=json non supporté
            if "unknown option" in result.stderr.lower() \
                    or "invalid option" in result.stderr.lower():
                return self._list_timers_text_fallback()
            raise RuntimeError(
                f"Erreur systemctl list-timers : {result.stderr}"
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return self._list_timers_text_fallback()

        timers = []
        for entry in data:
            timers.append({
                "unit": entry.get("unit", ""),
                "activates": entry.get("activates", ""),
                "next": entry.get("next", ""),
                "left": entry.get("left", ""),
                "last": entry.get("last", ""),
                "passed": entry.get("passed", ""),
            })
        return timers

    def _list_timers_text_fallback(self) -> list[dict[str, str]]:
        """Fallback texte pour list_timers sur vieux systemd.

        Returns:
            Liste de dictionnaires avec les infos des timers.

        Raises:
            RuntimeError: Si l'exécution de systemctl échoue.
        """
        try:
            result = subprocess.run(
                ["systemctl", "list-timers", "--no-pager",
                 "--plain"],
                capture_output=True,
                text=True,
                check=False
            )
        except (FileNotFoundError, OSError) as e:
            raise RuntimeError(
                f"Impossible d'exécuter systemctl : {e}"
            ) from e

        if result.returncode != 0:
            raise RuntimeError(
                f"Erreur systemctl list-timers : {result.stderr}"
            )

        timers = []
        lines = result.stdout.strip().split("\n")
        for line in lines[1:]:
            if not line.strip() or line.startswith(" "):
                continue
            parts = line.split()
            if len(parts) >= 2:
                timers.append({
                    "unit": parts[-2],
                    "activates": parts[-1],
                })
        return timers

    def is_timer_active(self, timer_name: str) -> bool:
        """
        Vérifie si un timer est actif.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si actif, False sinon
        """
        return self.get_timer_status(timer_name) == "active"
