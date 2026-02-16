"""Exécuteur de commandes systemctl."""

import subprocess

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.validators import validate_unit_name


class SystemdExecutor:
    """Exécuteur de commandes systemctl.

    Encapsule toutes les opérations bas niveau systemctl
    (daemon-reload, enable, disable, start, stop, status).

    Attributes:
        logger: Instance de Logger pour le logging.
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialise l'exécuteur systemd.

        Args:
            logger: Instance de Logger pour le logging
        """
        self.logger = logger

    def _run_systemctl(
        self,
        args: list[str],
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
        return subprocess.run(
            cmd, check=check, capture_output=True, text=True
        )

    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd (daemon-reload).

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

    def enable_unit(self, unit_name: str, now: bool = True) -> bool:
        """
        Active une unité systemd.

        Args:
            unit_name: Nom de l'unité (ex: "media-nas.mount")
            now: Démarrer immédiatement l'unité

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            args = ["enable"]
            if now:
                args.append("--now")
            args.append(unit_name)
            self._run_systemctl(args)
            msg = f"Unité {unit_name} activée"
            if now:
                msg += " et démarrée"
            self.logger.log_info(f"{msg} avec succès.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors de l'activation de l'unité {unit_name}: {e}"
            )
            return False

    def disable_unit(
        self,
        unit_name: str,
        now: bool = True,
        ignore_errors: bool = False
    ) -> bool:
        """
        Désactive une unité systemd.

        Args:
            unit_name: Nom de l'unité
            now: Arrêter immédiatement l'unité
            ignore_errors: Ignorer les erreurs (unité inexistante, etc.)

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            args = ["disable"]
            if now:
                args.append("--now")
            args.append(unit_name)
            self._run_systemctl(args, check=not ignore_errors)
            self.logger.log_info(
                f"Unité {unit_name} désactivée et arrêtée."
            )
            return True
        except subprocess.CalledProcessError as e:
            if ignore_errors:
                self.logger.log_warning(
                    f"Impossible de désactiver {unit_name}: {e}"
                )
                return True
            self.logger.log_error(
                f"Erreur lors de la désactivation de {unit_name}: {e}"
            )
            return False

    def start_unit(self, unit_name: str) -> bool:
        """
        Démarre une unité systemd.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            self._run_systemctl(["start", unit_name])
            self.logger.log_info(f"Unité {unit_name} démarrée.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors du démarrage de {unit_name}: {e}"
            )
            return False

    def stop_unit(self, unit_name: str) -> bool:
        """
        Arrête une unité systemd.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            self._run_systemctl(["stop", unit_name])
            self.logger.log_info(f"Unité {unit_name} arrêtée.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors de l'arrêt de {unit_name}: {e}"
            )
            return False

    def restart_unit(self, unit_name: str) -> bool:
        """
        Redémarre une unité systemd.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si succès, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            self._run_systemctl(["restart", unit_name])
            self.logger.log_info(f"Unité {unit_name} redémarrée.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors du redémarrage de {unit_name}: {e}"
            )
            return False

    def get_status(self, unit_name: str) -> str | None:
        """
        Récupère le statut d'une unité systemd.

        Args:
            unit_name: Nom de l'unité

        Returns:
            Statut de l'unité (active, inactive, failed, etc.) ou None
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            result = self._run_systemctl(
                ["is-active", unit_name],
                check=False
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, OSError) as e:
            self.logger.log_error(
                f"Erreur lors de la récupération du statut "
                f"de {unit_name}: {e}"
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

    def is_enabled(self, unit_name: str) -> bool:
        """
        Vérifie si une unité systemd est activée au démarrage.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si activée, False sinon
        """
        validate_unit_name(unit_name.rsplit(".", 1)[0])
        try:
            result = self._run_systemctl(
                ["is-enabled", unit_name],
                check=False
            )
            return result.stdout.strip() == "enabled"
        except (subprocess.SubprocessError, OSError) as e:
            self.logger.log_error(
                f"Erreur lors de la vérification de {unit_name}: {e}"
            )
            return False


class UserSystemdExecutor(SystemdExecutor):
    """Exécuteur de commandes systemctl --user.

    Encapsule toutes les opérations bas niveau systemctl pour les
    unités utilisateur (daemon-reload, enable, disable, start, stop, status).

    Les unités utilisateur ne nécessitent pas de privilèges root et sont
    stockées dans ~/.config/systemd/user/.

    Attributes:
        logger: Instance de Logger pour le logging.
    """

    def _run_systemctl(
        self,
        args: list[str],
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Exécute une commande systemctl --user.

        Args:
            args: Arguments de la commande systemctl
            check: Lever une exception si la commande échoue

        Returns:
            Résultat de la commande
        """
        cmd = ["systemctl", "--user"] + args
        return subprocess.run(
            cmd, check=check, capture_output=True, text=True
        )

    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd utilisateur (daemon-reload).

        Returns:
            True si succès, False sinon
        """
        try:
            self._run_systemctl(["daemon-reload"])
            self.logger.log_info(
                "Systemd utilisateur rechargé avec succès."
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                f"Erreur lors du rechargement de systemd utilisateur: {e}"
            )
            return False
