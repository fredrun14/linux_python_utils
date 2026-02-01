"""Implémentation Linux de la gestion des unités mount/automount systemd."""

import os
from pathlib import Path

from linux_python_utils.logging.base import Logger
from linux_python_utils.systemd.base import (
    MountUnitManager,
    MountConfig,
    AutomountConfig
)
from linux_python_utils.systemd.executor import SystemdExecutor


class LinuxMountUnitManager(MountUnitManager):
    """Implémentation Linux de la gestion des unités .mount et .automount.

    Génère et installe des fichiers unit systemd pour le montage
    de systèmes de fichiers (NFS, CIFS, SSHFS, etc.).

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
        Initialise le gestionnaire d'unités mount.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de SystemdExecutor pour les opérations systemctl
        """
        super().__init__(logger, executor)

    def path_to_unit_name(self, mount_path: str) -> str:
        """
        Convertit un chemin de montage en nom d'unité systemd.

        Exemple: /media/nas/backup → media-nas-backup

        Args:
            mount_path: Chemin du point de montage

        Returns:
            Nom de l'unité systemd (sans extension)
        """
        # Normalise le chemin et supprime le slash initial et final
        path = mount_path.strip("/")
        # Remplace les slashs par des tirets
        return path.replace("/", "-")

    def generate_mount_unit(self, config: MountConfig) -> str:
        """
        Génère le contenu d'un fichier .mount systemd.

        Args:
            config: Configuration du montage

        Returns:
            Contenu du fichier .mount
        """
        options_line = ""
        if config.options:
            options_line = f"Options={config.options}\n"

        return f"""[Unit]
Description={config.description}
After=network-online.target
Wants=network-online.target

[Mount]
What={config.what}
Where={config.where}
Type={config.type}
{options_line}
[Install]
WantedBy=multi-user.target
"""

    def generate_automount_unit(self, config: AutomountConfig) -> str:
        """
        Génère le contenu d'un fichier .automount systemd.

        Args:
            config: Configuration de l'automontage

        Returns:
            Contenu du fichier .automount
        """
        timeout_line = ""
        if config.timeout_idle_sec > 0:
            timeout_line = f"TimeoutIdleSec={config.timeout_idle_sec}\n"

        return f"""[Unit]
Description=Automontage {config.description}
Requires=network-online.target
After=network-online.target

[Automount]
Where={config.where}
{timeout_line}
[Install]
WantedBy=multi-user.target
"""

    def _ensure_mount_point(self, path: str) -> bool:
        """
        Crée le point de montage s'il n'existe pas.

        Args:
            path: Chemin du point de montage

        Returns:
            True si le répertoire existe ou a été créé, False sinon
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            self.logger.log_info(f"Point de montage créé: {path}")
            return True
        except PermissionError:
            self.logger.log_error(
                f"Permission refusée pour créer {path}. "
                "Exécution en tant que root requise."
            )
            return False
        except OSError as e:
            self.logger.log_error(
                f"Erreur lors de la création du point de montage {path}: {e}"
            )
            return False

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

    def install_mount_unit(
        self,
        config: MountConfig,
        with_automount: bool = False,
        automount_timeout: int = 0
    ) -> bool:
        """
        Installe une unité .mount (et optionnellement .automount).

        Args:
            config: Configuration du montage
            with_automount: Créer aussi une unité .automount
            automount_timeout: Délai d'inactivité avant démontage (secondes)

        Returns:
            True si succès, False sinon
        """
        unit_name = self.path_to_unit_name(config.where)

        # Créer le point de montage
        if not self._ensure_mount_point(config.where):
            return False

        # Générer et écrire le fichier .mount
        mount_content = self.generate_mount_unit(config)
        if not self._write_unit_file(f"{unit_name}.mount", mount_content):
            return False

        # Optionnellement créer le fichier .automount
        if with_automount:
            automount_config = AutomountConfig(
                description=config.description,
                where=config.where,
                timeout_idle_sec=automount_timeout
            )
            automount_content = self.generate_automount_unit(automount_config)
            if not self._write_unit_file(
                f"{unit_name}.automount",
                automount_content
            ):
                return False

        # Recharger systemd
        if not self.reload_systemd():
            return False

        self.logger.log_info(
            f"Unité de montage installée pour {config.where}"
        )
        return True

    def enable_mount(
        self,
        mount_path: str,
        with_automount: bool = False
    ) -> bool:
        """
        Active une unité .mount (ou .automount si spécifié).

        Args:
            mount_path: Chemin du point de montage
            with_automount: Activer l'unité .automount au lieu de .mount

        Returns:
            True si succès, False sinon
        """
        unit_name = self.path_to_unit_name(mount_path)

        if with_automount:
            unit = f"{unit_name}.automount"
        else:
            unit = f"{unit_name}.mount"

        return self.enable(unit)

    def disable_mount(self, mount_path: str) -> bool:
        """
        Désactive et arrête les unités .mount et .automount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si succès, False sinon
        """
        unit_name = self.path_to_unit_name(mount_path)

        # Désactiver d'abord l'automount s'il existe (ignorer erreurs)
        automount_unit = f"{unit_name}.automount"
        self.disable(automount_unit, ignore_errors=True)

        # Désactiver le mount
        mount_unit = f"{unit_name}.mount"
        return self.disable(mount_unit)

    def remove_mount_unit(self, mount_path: str) -> bool:
        """
        Supprime les fichiers .mount et .automount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si succès, False sinon
        """
        unit_name = self.path_to_unit_name(mount_path)

        # D'abord désactiver les unités
        self.disable_mount(mount_path)

        # Supprimer les fichiers
        success = True
        if not self._remove_unit_file(f"{unit_name}.mount"):
            success = False
        if not self._remove_unit_file(f"{unit_name}.automount"):
            success = False

        # Recharger systemd
        if success:
            self.reload_systemd()
            self.logger.log_info(
                f"Unités de montage supprimées pour {mount_path}"
            )

        return success

    def get_mount_status(self, mount_path: str) -> str | None:
        """
        Récupère le statut d'une unité .mount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            Statut de l'unité ou None si erreur
        """
        unit_name = self.path_to_unit_name(mount_path)
        return self.get_status(f"{unit_name}.mount")

    def is_mounted(self, mount_path: str) -> bool:
        """
        Vérifie si un point de montage est actif.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si monté, False sinon
        """
        return self.get_mount_status(mount_path) == "active"
