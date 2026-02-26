"""Implémentation Linux de la gestion des unités timer utilisateur."""

import json
import subprocess  # nosec B404

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import UserTimerUnitManager, TimerConfig
from linux_python_utils.systemd.executor import UserSystemdExecutor
from linux_python_utils.systemd.validators import validate_unit_name


class LinuxUserTimerUnitManager(UserTimerUnitManager):
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

    def enable_timer(self, timer_name: str) -> bool:
        """
        Active un timer utilisateur.

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
        Désactive un timer utilisateur.

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
        Supprime un fichier .timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(timer_name)
        # D'abord désactiver le timer
        if not self.disable_timer(timer_name):
            self.logger.log_warning(
                f"disable_timer échoué pour {timer_name!r} "
                "(unité peut-être déjà inactive) — "
                "suppression du fichier unit quand même"
            )

        # Supprimer le fichier
        if not self._remove_unit_file(f"{timer_name}.timer"):
            return False

        # Recharger systemd utilisateur
        self.reload_systemd()
        self.logger.log_info(
            f"Timer utilisateur {timer_name}.timer supprimé"
        )
        return True

    def get_timer_status(self, timer_name: str) -> str | None:
        """
        Récupère le statut d'un timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            Statut du timer ou None si erreur
        """
        validate_unit_name(timer_name)
        return self.get_status(f"{timer_name}.timer")

    def list_timers(self) -> list[dict[str, str]]:
        """Liste tous les timers utilisateur actifs.

        Utilise ``--output=json`` pour un parsing fiable, avec
        fallback sur le parsing texte si le format JSON n'est pas
        supporté par la version de systemd installée.

        Returns:
            Liste de dictionnaires avec les infos des timers.

        Raises:
            RuntimeError: Si l'exécution de systemctl échoue.
        """
        try:
            result = subprocess.run(  # nosec B603 B607
                ["systemctl", "--user", "list-timers",
                 "--no-pager", "--output=json"],
                capture_output=True,
                text=True,
                check=False
            )
        except (FileNotFoundError, OSError) as e:
            raise RuntimeError(
                f"Impossible d'exécuter systemctl : {e}"
            ) from e

        if result.returncode != 0:
            if "unknown option" in result.stderr.lower() \
                    or "invalid option" in result.stderr.lower():
                return self._list_timers_text_fallback()
            raise RuntimeError(
                "Erreur systemctl list-timers --user : "
                f"{result.stderr}"
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
            result = subprocess.run(  # nosec B603 B607
                ["systemctl", "--user", "list-timers",
                 "--no-pager", "--plain"],
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
                "Erreur systemctl list-timers --user : "
                f"{result.stderr}"
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
        Vérifie si un timer utilisateur est actif.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si actif, False sinon
        """
        return self.get_timer_status(timer_name) == "active"
