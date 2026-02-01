"""Module de gestion des unités systemd.

Ce module fournit des classes pour gérer les unités systemd:

Unités système (root):
- SystemdExecutor: Exécuteur de commandes systemctl
- LinuxMountUnitManager: Gestion des unités .mount et .automount
- LinuxTimerUnitManager: Gestion des unités .timer
- LinuxServiceUnitManager: Gestion des unités .service

Unités utilisateur (sans root):
- UserSystemdExecutor: Exécuteur de commandes systemctl --user
- LinuxUserTimerUnitManager: Gestion des unités .timer utilisateur
- LinuxUserServiceUnitManager: Gestion des unités .service utilisateur

Architecture:
    SystemdExecutor/UserSystemdExecutor est injecté dans les différents
    UnitManagers pour centraliser les opérations systemctl.

Exemple d'utilisation (système):
    from linux_python_utils import FileLogger
    from linux_python_utils.systemd import (
        SystemdExecutor,
        LinuxMountUnitManager,
        MountConfig
    )

    logger = FileLogger("/var/log/app.log")
    executor = SystemdExecutor(logger)
    mount_manager = LinuxMountUnitManager(logger, executor)

    config = MountConfig(
        description="Partage NAS",
        what="192.168.1.10:/share",
        where="/media/nas",
        type="nfs",
        options="rw,soft"
    )
    mount_manager.install_mount_unit(config, with_automount=True)

Exemple d'utilisation (utilisateur):
    from linux_python_utils import FileLogger
    from linux_python_utils.systemd import (
        UserSystemdExecutor,
        LinuxUserTimerUnitManager,
        TimerConfig
    )

    logger = FileLogger("~/.local/log/app.log")
    executor = UserSystemdExecutor(logger)
    timer_manager = LinuxUserTimerUnitManager(logger, executor)

    config = TimerConfig(
        description="Backup quotidien",
        unit="backup.service",
        on_calendar="daily",
        persistent=True
    )
    timer_manager.install_timer_unit(config)
"""

# Classes abstraites et configurations
from linux_python_utils.systemd.base import (
    # Système
    UnitManager,
    MountUnitManager,
    TimerUnitManager,
    ServiceUnitManager,
    # Utilisateur
    UserUnitManager,
    UserTimerUnitManager,
    UserServiceUnitManager,
    # Configurations
    MountConfig,
    AutomountConfig,
    TimerConfig,
    ServiceConfig,
)

# Exécuteurs systemctl
from linux_python_utils.systemd.executor import (
    SystemdExecutor,
    UserSystemdExecutor,
)

# Implémentations Linux système
from linux_python_utils.systemd.mount import LinuxMountUnitManager
from linux_python_utils.systemd.timer import LinuxTimerUnitManager
from linux_python_utils.systemd.service import LinuxServiceUnitManager

# Implémentations Linux utilisateur
from linux_python_utils.systemd.user_timer import LinuxUserTimerUnitManager
from linux_python_utils.systemd.user_service import LinuxUserServiceUnitManager

# Rétrocompatibilité avec l'ancienne API
# (LinuxSystemdServiceManager est remplacé par SystemdExecutor)
LinuxSystemdServiceManager = SystemdExecutor

__all__ = [
    # Classes abstraites système
    "UnitManager",
    "MountUnitManager",
    "TimerUnitManager",
    "ServiceUnitManager",
    # Classes abstraites utilisateur
    "UserUnitManager",
    "UserTimerUnitManager",
    "UserServiceUnitManager",
    # Configurations
    "MountConfig",
    "AutomountConfig",
    "TimerConfig",
    "ServiceConfig",
    # Exécuteurs
    "SystemdExecutor",
    "UserSystemdExecutor",
    # Implémentations système
    "LinuxMountUnitManager",
    "LinuxTimerUnitManager",
    "LinuxServiceUnitManager",
    # Implémentations utilisateur
    "LinuxUserTimerUnitManager",
    "LinuxUserServiceUnitManager",
    # Rétrocompatibilité
    "LinuxSystemdServiceManager",
]
