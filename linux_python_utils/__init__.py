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
from linux_python_utils.config import load_config, ConfigurationManager
from linux_python_utils.filesystem import (
    FileManager,
    LinuxFileManager,
    FileBackup,
    LinuxFileBackup
)
from linux_python_utils.systemd import (
    SystemdServiceManager,
    LinuxSystemdServiceManager
)
from linux_python_utils.integrity import (
    IntegrityChecker,
    SHA256IntegrityChecker,
    calculate_checksum
)

__all__ = [
    # Logging
    "Logger",
    "FileLogger",
    # Config
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
    # Integrity
    "IntegrityChecker",
    "SHA256IntegrityChecker",
    "calculate_checksum",
]
