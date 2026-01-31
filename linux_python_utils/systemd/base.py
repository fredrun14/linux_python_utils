"""Interface abstraite pour la gestion des services systemd."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MountConfig:
    """Configuration pour une unité .mount systemd.

    Attributes:
        description: Description de l'unité pour systemd.
        what: Source du montage (ex: "192.168.1.10:/share", "//server/share").
        where: Chemin du point de montage local.
        type: Type de système de fichiers (nfs, cifs, sshfs, ext4, etc.).
        options: Options de montage (défaut: chaîne vide).
    """

    description: str
    what: str
    where: str
    type: str
    options: str = ""


@dataclass
class AutomountConfig:
    """Configuration pour une unité .automount systemd.

    Attributes:
        description: Description de l'unité pour systemd.
        where: Chemin du point de montage local.
        timeout_idle_sec: Délai d'inactivité avant démontage automatique
            en secondes (0 = pas de démontage automatique).
    """

    description: str
    where: str
    timeout_idle_sec: int = 0


class MountUnitManager(ABC):
    """Interface pour la gestion des unités .mount et .automount systemd."""

    @abstractmethod
    def path_to_unit_name(self, mount_path: str) -> str:
        """
        Convertit un chemin de montage en nom d'unité systemd.

        Exemple: /media/nas/backup → media-nas-backup

        Args:
            mount_path: Chemin du point de montage

        Returns:
            Nom de l'unité systemd (sans extension)
        """
        pass

    @abstractmethod
    def generate_mount_unit(self, config: MountConfig) -> str:
        """
        Génère le contenu d'un fichier .mount systemd.

        Args:
            config: Configuration du montage

        Returns:
            Contenu du fichier .mount
        """
        pass

    @abstractmethod
    def generate_automount_unit(self, config: AutomountConfig) -> str:
        """
        Génère le contenu d'un fichier .automount systemd.

        Args:
            config: Configuration de l'automontage

        Returns:
            Contenu du fichier .automount
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def enable_mount(
        self, mount_path: str, with_automount: bool = False
    ) -> bool:
        """
        Active une unité .mount (ou .automount si spécifié).

        Args:
            mount_path: Chemin du point de montage
            with_automount: Activer l'unité .automount au lieu de .mount

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_mount(self, mount_path: str) -> bool:
        """
        Désactive et arrête les unités .mount et .automount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def remove_mount_unit(self, mount_path: str) -> bool:
        """
        Supprime les fichiers .mount et .automount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si succès, False sinon
        """
        pass


class SystemdServiceManager(ABC):
    """Interface pour la gestion des services systemd."""

    @abstractmethod
    def enable_timer(self, timer_name: str) -> bool:
        """
        Active et démarre un timer systemd.

        Args:
            timer_name: Nom du timer (ex: "flatpak-update.timer")

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def enable_unit(self, unit_name: str) -> bool:
        """
        Active et démarre une unité systemd.

        Args:
            unit_name: Nom de l'unité (ex: "media-nas.mount")

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_unit(
        self, unit_name: str, ignore_errors: bool = False
    ) -> bool:
        """
        Désactive et arrête une unité systemd.

        Args:
            unit_name: Nom de l'unité
            ignore_errors: Ignorer les erreurs (unité inexistante, etc.)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd (daemon-reload).

        Returns:
            True si succès, False sinon
        """
        pass
