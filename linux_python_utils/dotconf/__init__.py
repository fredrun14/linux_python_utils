"""Module DotConf pour la gestion de fichiers de configuration INI.

Ce module fournit des outils pour représenter et manipuler des fichiers
de configuration au format INI (.conf) avec :
- Validation externe des valeurs (depuis TOML, dictionnaire, etc.)
- Dataclasses immuables pour la représentation des sections
- Gestion robuste des opérations lecture/écriture

Classes principales:
    - IniSection: Interface abstraite pour une section INI
    - IniConfig: Interface abstraite pour un fichier INI complet
    - IniConfigManager: Interface abstraite pour la gestion de fichiers
    - ValidatedSection: Dataclass de base avec validation externe
    - LinuxIniConfigManager: Implémentation du gestionnaire de fichiers

Fonctions utilitaires:
    - parse_validator: Convertit un validateur brut en fonction/liste
    - build_validators: Construit un dictionnaire de validateurs

Example:
    >>> from dataclasses import dataclass
    >>> from linux_python_utils.dotconf import (
    ...     ValidatedSection, LinuxIniConfigManager
    ... )
    >>> from linux_python_utils import FileLogger
    >>>
    >>> @dataclass(frozen=True)
    ... class CommandsSection(ValidatedSection):
    ...     upgrade_type: str = "default"
    ...     download_updates: str = "yes"
    ...
    ...     @staticmethod
    ...     def section_name() -> str:
    ...         return "commands"
    >>>
    >>> # Injecter les validators depuis le TOML
    >>> CommandsSection.set_validators({
    ...     "upgrade_type": ["default", "security"],
    ...     "download_updates": ["yes", "no"],
    ... })
    >>>
    >>> # Créer une section validée
    >>> section = CommandsSection(
    ...     upgrade_type="security", download_updates="yes"
    ... )
    >>>
    >>> # Écrire dans un fichier
    >>> logger = FileLogger("/var/log/test.log")
    >>> manager = LinuxIniConfigManager(logger)
    >>> manager.write_section(Path("/etc/test.conf"), section)
"""

from linux_python_utils.dotconf.base import (
    IniConfig,
    IniConfigManager,
    IniSection,
)
from linux_python_utils.dotconf.manager import LinuxIniConfigManager
from linux_python_utils.dotconf.section import (
    ValidatedSection,
    build_validators,
    parse_validator,
)

__all__ = [
    # Interfaces abstraites
    "IniSection",
    "IniConfig",
    "IniConfigManager",
    # Implémentations
    "ValidatedSection",
    "LinuxIniConfigManager",
    # Fonctions utilitaires
    "parse_validator",
    "build_validators",
]
