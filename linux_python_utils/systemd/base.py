"""Interfaces abstraites pour la gestion des unités systemd."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linux_python_utils.logging.base import Logger
    from linux_python_utils.systemd.executor import SystemdExecutor


# =============================================================================
# Dataclasses de configuration
# =============================================================================

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


@dataclass
class TimerConfig:
    """Configuration pour une unité .timer systemd.

    Attributes:
        description: Description de l'unité pour systemd.
        unit: Nom de l'unité à déclencher (ex: "backup.service").
        on_calendar: Expression de calendrier (ex: "daily", "*-*-* 06:00:00").
        on_boot_sec: Délai après le démarrage (ex: "5min").
        on_unit_active_sec: Délai après la dernière activation de l'unité.
        persistent: Rattraper les exécutions manquées après un arrêt.
        randomized_delay_sec: Délai aléatoire ajouté (ex: "1h").
    """

    description: str
    unit: str
    on_calendar: str = ""
    on_boot_sec: str = ""
    on_unit_active_sec: str = ""
    persistent: bool = False
    randomized_delay_sec: str = ""


@dataclass
class ServiceConfig:
    """Configuration pour une unité .service systemd.

    Attributes:
        description: Description de l'unité pour systemd.
        exec_start: Commande à exécuter au démarrage.
        type: Type de service (simple, oneshot, forking, notify, dbus, idle).
        user: Utilisateur sous lequel exécuter le service.
        group: Groupe sous lequel exécuter le service.
        working_directory: Répertoire de travail.
        environment: Variables d'environnement (dict).
        restart: Politique de redémarrage (no, always, on-failure, etc.).
        restart_sec: Délai avant redémarrage en secondes.
        wanted_by: Cible d'installation (défaut: multi-user.target).
    """

    description: str
    exec_start: str
    type: str = "simple"
    user: str = ""
    group: str = ""
    working_directory: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    restart: str = "no"
    restart_sec: int = 0
    wanted_by: str = "multi-user.target"


# =============================================================================
# Classes abstraites
# =============================================================================

class UnitManager(ABC):
    """Classe de base abstraite pour tous les gestionnaires d'unités systemd.

    Fournit les opérations communes à tous les types d'unités via
    l'injection d'un SystemdExecutor.

    Attributes:
        logger: Instance de Logger pour le logging.
        executor: Instance de SystemdExecutor pour les opérations systemctl.
        SYSTEMD_UNIT_PATH: Chemin du répertoire des unités systemd.
    """

    SYSTEMD_UNIT_PATH: str = "/etc/systemd/system"

    def __init__(
        self,
        logger: "Logger",
        executor: "SystemdExecutor"
    ) -> None:
        """
        Initialise le gestionnaire d'unités.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de SystemdExecutor pour les opérations systemctl
        """
        self.logger = logger
        self.executor = executor

    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd (daemon-reload).

        Returns:
            True si succès, False sinon
        """
        return self.executor.reload_systemd()

    def enable(self, unit_name: str) -> bool:
        """
        Active une unité systemd.

        Args:
            unit_name: Nom de l'unité (ex: "flatpak-update.timer")

        Returns:
            True si succès, False sinon
        """
        return self.executor.enable_unit(unit_name)

    def disable(self, unit_name: str, ignore_errors: bool = False) -> bool:
        """
        Désactive une unité systemd.

        Args:
            unit_name: Nom de l'unité (ex: "media-nas.mount")
            ignore_errors: Ignorer les erreurs (unité inexistante, etc.)

        Returns:
            True si succès, False sinon
        """
        return self.executor.disable_unit(
            unit_name, ignore_errors=ignore_errors
        )

    def get_status(self, unit_name: str) -> str | None:
        """
        Récupère le statut d'une unité.

        Args:
            unit_name: Nom de l'unité (ex: "media-nas.mount")

        Returns:
            Statut de l'unité ou None si erreur
        """
        return self.executor.get_status(unit_name)

    def is_active(self, unit_name: str) -> bool:
        """
        Vérifie si une unité est active.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si active, False sinon
        """
        return self.executor.is_active(unit_name)


class MountUnitManager(UnitManager):
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

    @abstractmethod
    def get_mount_status(self, mount_path: str) -> str | None:
        """
        Récupère le statut d'une unité .mount.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            Statut de l'unité ou None si erreur
        """
        pass

    @abstractmethod
    def is_mounted(self, mount_path: str) -> bool:
        """
        Vérifie si un point de montage est actif.

        Args:
            mount_path: Chemin du point de montage

        Returns:
            True si monté, False sinon
        """
        pass


class TimerUnitManager(UnitManager):
    """Interface pour la gestion des unités .timer systemd."""

    @abstractmethod
    def generate_timer_unit(self, config: TimerConfig) -> str:
        """
        Génère le contenu d'un fichier .timer systemd.

        Args:
            config: Configuration du timer

        Returns:
            Contenu du fichier .timer
        """
        pass

    @abstractmethod
    def install_timer_unit(self, config: TimerConfig) -> bool:
        """
        Installe une unité .timer.

        Args:
            config: Configuration du timer

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def enable_timer(self, timer_name: str) -> bool:
        """
        Active un timer systemd.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_timer(self, timer_name: str) -> bool:
        """
        Désactive un timer systemd.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def remove_timer_unit(self, timer_name: str) -> bool:
        """
        Supprime un fichier .timer.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def get_timer_status(self, timer_name: str) -> str | None:
        """
        Récupère le statut d'un timer.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            Statut du timer ou None si erreur
        """
        pass

    @abstractmethod
    def list_timers(self) -> list[dict[str, str]]:
        """
        Liste tous les timers actifs.

        Returns:
            Liste de dictionnaires avec les infos des timers
        """
        pass


class ServiceUnitManager(UnitManager):
    """Interface pour la gestion des unités .service systemd."""

    @abstractmethod
    def generate_service_unit(self, config: ServiceConfig) -> str:
        """
        Génère le contenu d'un fichier .service systemd.

        Args:
            config: Configuration du service

        Returns:
            Contenu du fichier .service
        """
        pass

    @abstractmethod
    def install_service_unit(self, config: ServiceConfig) -> bool:
        """
        Installe une unité .service.

        Args:
            config: Configuration du service

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def stop_service(self, service_name: str) -> bool:
        """
        Arrête un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def restart_service(self, service_name: str) -> bool:
        """
        Redémarre un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def enable_service(self, service_name: str) -> bool:
        """
        Active un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_service(self, service_name: str) -> bool:
        """
        Désactive un service systemd.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def remove_service_unit(self, service_name: str) -> bool:
        """
        Supprime un fichier .service.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def get_service_status(self, service_name: str) -> str | None:
        """
        Récupère le statut d'un service.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            Statut du service ou None si erreur
        """
        pass


# =============================================================================
# Classes abstraites pour les unités utilisateur
# =============================================================================

class UserUnitManager(ABC):
    """Classe de base pour les gestionnaires d'unités systemd utilisateur.

    Les unités utilisateur sont stockées dans ~/.config/systemd/user/
    et ne nécessitent pas de privilèges root.

    Attributes:
        logger: Instance de Logger pour le logging.
        executor: Instance de UserSystemdExecutor pour les opérations.
        SYSTEMD_USER_UNIT_PATH: Chemin du répertoire des unités utilisateur.
    """

    SYSTEMD_USER_UNIT_PATH: str = "~/.config/systemd/user"

    def __init__(
        self,
        logger: "Logger",
        executor: "SystemdExecutor"
    ) -> None:
        """
        Initialise le gestionnaire d'unités utilisateur.

        Args:
            logger: Instance de Logger pour le logging
            executor: Instance de UserSystemdExecutor pour les opérations
        """
        self.logger = logger
        self.executor = executor
        # Expansion du chemin utilisateur
        import os
        self._unit_path = os.path.expanduser(self.SYSTEMD_USER_UNIT_PATH)

    @property
    def unit_path(self) -> str:
        """Retourne le chemin absolu du répertoire des unités."""
        return self._unit_path

    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd utilisateur (daemon-reload).

        Returns:
            True si succès, False sinon
        """
        return self.executor.reload_systemd()

    def enable(self, unit_name: str) -> bool:
        """
        Active une unité systemd utilisateur.

        Args:
            unit_name: Nom de l'unité (ex: "backup.timer")

        Returns:
            True si succès, False sinon
        """
        return self.executor.enable_unit(unit_name)

    def disable(self, unit_name: str, ignore_errors: bool = False) -> bool:
        """
        Désactive une unité systemd utilisateur.

        Args:
            unit_name: Nom de l'unité
            ignore_errors: Ignorer les erreurs (unité inexistante, etc.)

        Returns:
            True si succès, False sinon
        """
        return self.executor.disable_unit(
            unit_name, ignore_errors=ignore_errors
        )

    def get_status(self, unit_name: str) -> str | None:
        """
        Récupère le statut d'une unité utilisateur.

        Args:
            unit_name: Nom de l'unité

        Returns:
            Statut de l'unité ou None si erreur
        """
        return self.executor.get_status(unit_name)

    def is_active(self, unit_name: str) -> bool:
        """
        Vérifie si une unité utilisateur est active.

        Args:
            unit_name: Nom de l'unité

        Returns:
            True si active, False sinon
        """
        return self.executor.is_active(unit_name)


class UserTimerUnitManager(UserUnitManager):
    """Interface pour la gestion des unités .timer utilisateur."""

    @abstractmethod
    def generate_timer_unit(self, config: TimerConfig) -> str:
        """
        Génère le contenu d'un fichier .timer systemd.

        Args:
            config: Configuration du timer

        Returns:
            Contenu du fichier .timer
        """
        pass

    @abstractmethod
    def install_timer_unit(self, config: TimerConfig) -> bool:
        """
        Installe une unité .timer utilisateur.

        Args:
            config: Configuration du timer

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def enable_timer(self, timer_name: str) -> bool:
        """
        Active un timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_timer(self, timer_name: str) -> bool:
        """
        Désactive un timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension .timer)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def remove_timer_unit(self, timer_name: str) -> bool:
        """
        Supprime un fichier .timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def get_timer_status(self, timer_name: str) -> str | None:
        """
        Récupère le statut d'un timer utilisateur.

        Args:
            timer_name: Nom du timer (sans extension)

        Returns:
            Statut du timer ou None si erreur
        """
        pass

    @abstractmethod
    def list_timers(self) -> list[dict[str, str]]:
        """
        Liste tous les timers utilisateur actifs.

        Returns:
            Liste de dictionnaires avec les infos des timers
        """
        pass


class UserServiceUnitManager(UserUnitManager):
    """Interface pour la gestion des unités .service utilisateur."""

    @abstractmethod
    def generate_service_unit(self, config: ServiceConfig) -> str:
        """
        Génère le contenu d'un fichier .service systemd.

        Args:
            config: Configuration du service

        Returns:
            Contenu du fichier .service
        """
        pass

    @abstractmethod
    def install_service_unit(self, config: ServiceConfig) -> bool:
        """
        Installe une unité .service utilisateur.

        Args:
            config: Configuration du service

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def start_service(self, service_name: str) -> bool:
        """
        Démarre un service utilisateur.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def stop_service(self, service_name: str) -> bool:
        """
        Arrête un service utilisateur.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def restart_service(self, service_name: str) -> bool:
        """
        Redémarre un service utilisateur.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def enable_service(self, service_name: str) -> bool:
        """
        Active un service utilisateur.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def disable_service(self, service_name: str) -> bool:
        """
        Désactive un service utilisateur.

        Args:
            service_name: Nom du service (sans extension .service)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def remove_service_unit(self, service_name: str) -> bool:
        """
        Supprime un fichier .service utilisateur.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def get_service_status(self, service_name: str) -> str | None:
        """
        Récupère le statut d'un service utilisateur.

        Args:
            service_name: Nom du service (sans extension)

        Returns:
            Statut du service ou None si erreur
        """
        pass
