"""
Linux Python Utils - Bibliothèque utilitaire pour systèmes Linux.

Modules disponibles:
- logging: Gestion des logs (Logger, FileLogger)
- config: Chargement de configuration (TOML, JSON)
- filesystem: Opérations sur fichiers (FileManager, FileBackup)
- systemd: Gestion des services systemd
- integrity: Vérification d'intégrité (checksums)
- dotconf: Gestion de fichiers de configuration INI (.conf)
- notification: Configuration des notifications desktop (NotificationConfig)
- scripts: Génération de scripts bash (BashScriptConfig)
- commands: Exécution de commandes système (CommandBuilder,
  LinuxCommandExecutor)
- validation: Validation de chemins et données (Validator, PathChecker)
- network: Gestion des peripheriques reseau (scanners, inventaire,
  DHCP, DNS, rapports)
"""

__version__ = "1.0.0"

from linux_python_utils.logging import Logger, FileLogger
from linux_python_utils.config import (
    ConfigManager,
    ConfigLoader,
    FileConfigLoader,
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
    # Installateur de tâches planifiées
    ScheduledTaskInstaller,
    SystemdScheduledTaskInstaller,
    # Chargeurs de configuration
    ServiceConfigLoader,
    TimerConfigLoader,
    MountConfigLoader,
    BashScriptConfigLoader,
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
from linux_python_utils.dotconf import (
    IniSection,
    IniConfig,
    IniConfigManager,
    ValidatedSection,
    LinuxIniConfigManager,
    parse_validator,
    build_validators,
)
from linux_python_utils.notification import NotificationConfig
from linux_python_utils.scripts import (
    BashScriptConfig,
    ScriptInstaller,
    BashScriptInstaller,
)
from linux_python_utils.commands import (
    CommandResult,
    CommandExecutor,
    CommandBuilder,
    CommandFormatter,
    PlainCommandFormatter,
    AnsiCommandFormatter,
    LinuxCommandExecutor,
)
from linux_python_utils.validation import (
    Validator,
    PathChecker,
)
from linux_python_utils.network import (
    # Modeles
    NetworkDevice,
    # Configuration
    NetworkConfig,
    DhcpRange,
    DnsConfig,
    # ABCs
    NetworkScanner,
    DeviceRepository,
    DhcpReservationManager,
    DnsManager,
    DeviceReporter,
    # Scanners
    LinuxArpScanner,
    LinuxNmapScanner,
    # Repository
    JsonDeviceRepository,
    # DHCP
    LinuxDhcpReservationManager,
    # DNS
    LinuxHostsFileManager,
    LinuxDnsmasqConfigGenerator,
    # Rapports
    ConsoleTableReporter,
    CsvReporter,
    JsonReporter,
    DiffReporter,
    # Validateurs
    validate_ipv4,
    validate_mac,
    validate_cidr,
    validate_hostname,
)

__all__ = [
    # Logging
    "Logger",
    "FileLogger",
    # Config
    "ConfigManager",
    "ConfigLoader",
    "FileConfigLoader",
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
    # Systemd - Installateur de tâches planifiées
    "ScheduledTaskInstaller",
    "SystemdScheduledTaskInstaller",
    # Systemd - Chargeurs de configuration
    "ServiceConfigLoader",
    "TimerConfigLoader",
    "MountConfigLoader",
    "BashScriptConfigLoader",
    # Systemd - Rétrocompatibilité
    "LinuxSystemdServiceManager",
    # Integrity
    "ChecksumCalculator",
    "HashLibChecksumCalculator",
    "IntegrityChecker",
    "SHA256IntegrityChecker",
    "calculate_checksum",
    # DotConf - Interfaces
    "IniSection",
    "IniConfig",
    "IniConfigManager",
    # DotConf - Implémentations
    "ValidatedSection",
    "LinuxIniConfigManager",
    # DotConf - Utilitaires
    "parse_validator",
    "build_validators",
    # Notification
    "NotificationConfig",
    # Scripts
    "BashScriptConfig",
    "ScriptInstaller",
    "BashScriptInstaller",
    # Commands - Structures de données
    "CommandResult",
    # Commands - Interface abstraite
    "CommandExecutor",
    # Commands - Constructeur
    "CommandBuilder",
    # Commands - Formateurs
    "CommandFormatter",
    "PlainCommandFormatter",
    "AnsiCommandFormatter",
    # Commands - Implémentation
    "LinuxCommandExecutor",
    # Validation
    "Validator",
    "PathChecker",
    # Network - Modeles
    "NetworkDevice",
    # Network - Configuration
    "NetworkConfig",
    "DhcpRange",
    "DnsConfig",
    # Network - ABCs
    "NetworkScanner",
    "DeviceRepository",
    "DhcpReservationManager",
    "DnsManager",
    "DeviceReporter",
    # Network - Scanners
    "LinuxArpScanner",
    "LinuxNmapScanner",
    # Network - Repository
    "JsonDeviceRepository",
    # Network - DHCP
    "LinuxDhcpReservationManager",
    # Network - DNS
    "LinuxHostsFileManager",
    "LinuxDnsmasqConfigGenerator",
    # Network - Rapports
    "ConsoleTableReporter",
    "CsvReporter",
    "JsonReporter",
    "DiffReporter",
    # Network - Validateurs
    "validate_ipv4",
    "validate_mac",
    "validate_cidr",
    "validate_hostname",
]
