"""Implémentation Linux de la gestion des unités timer systemd."""

import os
import subprocess

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import TimerUnitManager, TimerConfig
from linux_python_utils.systemd.executor import SystemdExecutor


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
        if os.path.islink(unit_path):
            self.logger.log_error(
                f"Refus d'écrire {unit_path} : lien symbolique détecté"
            )
            return False
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
        return self.get_status(f"{timer_name}.timer")

    def list_timers(self) -> list[dict[str, str]]:
        """
        Liste tous les timers actifs.

        Returns:
            Liste de dictionnaires avec les infos des timers
            (next, left, last, passed, unit, activates)
        """
        try:
            result = subprocess.run(
                ["systemctl", "list-timers", "--no-pager", "--plain"],
                capture_output=True,
                text=True,
                check=False
            )

            timers = []
            lines = result.stdout.strip().split("\n")

            # Ignorer l'en-tête et la ligne vide finale
            for line in lines[1:]:
                if not line.strip() or line.startswith(" "):
                    continue

                parts = line.split()
                if len(parts) >= 6:
                    # Format: NEXT LEFT LAST PASSED UNIT ACTIVATES
                    timers.append({
                        "left": parts[3] if len(parts) > 6 else parts[1],
                        "passed": parts[7] if len(parts) > 9 else parts[3],
                        "unit": parts[-2],
                        "activates": parts[-1]
                    })

            return timers

        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la récupération des timers: {e}"
            )
            return []

    def is_timer_active(self, timer_name: str) -> bool:
        """
        Vérifie si un timer est actif.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si actif, False sinon
        """
        return self.get_timer_status(timer_name) == "active"
