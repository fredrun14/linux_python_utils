"""
Linux Python Utils - Bibliothèque utilitaire pour systèmes Linux.

Modules disponibles:
- logging: Gestion des logs (Logger, FileLogger)
- config: Chargement de configuration (TOML, JSON)
- filesystem: Opérations sur fichiers (FileManager, FileBackup)
- systemd: Gestion des services systemd
- integrity: Vérification d'intégrité (checksums)
"""

__version__ = "0.1.0"

from linux_python_utils.logging import Logger, FileLogger
from linux_python_utils.config import (
    ConfigManager,
    ConfigLoader,
    FileConfigLoader,
    load_config,
    ConfigurationManager
)
from linux_python_utils.filesystem import (
    FileManager,
    LinuxFileManager,
    FileBackup,
    LinuxFileBackup
)
from linux_python_utils.systemd import (
    # Exécuteurs systemctl
    SystemdExecutor,
    UserSystemdExecutor,
    # Classes abstraites système
    UnitManager,
    MountUnitManager,
    TimerUnitManager,
    ServiceUnitManager,
    # Classes abstraites utilisateur
    UserUnitManager,
    UserTimerUnitManager,
    UserServiceUnitManager,
    # Configurations
    MountConfig,
    AutomountConfig,
    TimerConfig,
    ServiceConfig,
    # Implémentations système
    LinuxMountUnitManager,
    LinuxTimerUnitManager,
    LinuxServiceUnitManager,
    # Implémentations utilisateur
    LinuxUserTimerUnitManager,
    LinuxUserServiceUnitManager,
    # Rétrocompatibilité
    LinuxSystemdServiceManager,
)
from linux_python_utils.integrity import (
    ChecksumCalculator,
    HashLibChecksumCalculator,
    IntegrityChecker,
    SHA256IntegrityChecker,
    calculate_checksum
)

__all__ = [
    # Logging
    "Logger",
    "FileLogger",
    # Config
    "ConfigManager",
    "ConfigLoader",
    "FileConfigLoader",
    "load_config",
    "ConfigurationManager",
    # Filesystem
    "FileManager",
    "LinuxFileManager",
    "FileBackup",
    "LinuxFileBackup",
    # Systemd - Exécuteurs
    "SystemdExecutor",
    "UserSystemdExecutor",
    # Systemd - Classes abstraites système
    "UnitManager",
    "MountUnitManager",
    "TimerUnitManager",
    "ServiceUnitManager",
    # Systemd - Classes abstraites utilisateur
    "UserUnitManager",
    "UserTimerUnitManager",
    "UserServiceUnitManager",
    # Systemd - Configurations
    "MountConfig",
    "AutomountConfig",
    "TimerConfig",
    "ServiceConfig",
    # Systemd - Implémentations système
    "LinuxMountUnitManager",
    "LinuxTimerUnitManager",
    "LinuxServiceUnitManager",
    # Systemd - Implémentations utilisateur
    "LinuxUserTimerUnitManager",
    "LinuxUserServiceUnitManager",
    # Systemd - Rétrocompatibilité
    "LinuxSystemdServiceManager",
    # Integrity
    "ChecksumCalculator",
    "HashLibChecksumCalculator",
    "IntegrityChecker",
    "SHA256IntegrityChecker",
    "calculate_checksum",
]
