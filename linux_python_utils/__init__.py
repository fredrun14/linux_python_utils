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
    SystemdServiceManager,
    LinuxSystemdServiceManager,
    MountUnitManager,
    MountConfig,
    AutomountConfig,
    LinuxMountUnitManager
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
    # Systemd
    "SystemdServiceManager",
    "LinuxSystemdServiceManager",
    "MountUnitManager",
    "MountConfig",
    "AutomountConfig",
    "LinuxMountUnitManager",
    # Integrity
    "ChecksumCalculator",
    "HashLibChecksumCalculator",
    "IntegrityChecker",
    "SHA256IntegrityChecker",
    "calculate_checksum",
]
