"""Gestionnaire de fichiers de configuration INI.

Ce module fournit LinuxIniConfigManager, une implémentation robuste
pour la lecture, l'écriture et la mise à jour de fichiers INI.
"""

import configparser
from io import StringIO
from pathlib import Path
from typing import Any

from linux_python_utils.dotconf.base import (
    IniConfig,
    IniConfigManager,
    IniSection,
)
from linux_python_utils.logging.base import Logger


class LinuxIniConfigManager(IniConfigManager):
    """Gestionnaire de fichiers de configuration INI pour Linux.

    Utilise configparser pour les opérations de lecture/écriture
    avec support de logging et validation optionnelle.

    Attributes:
        logger: Instance de Logger pour tracer les opérations.

    Example:
        >>> from linux_python_utils import FileLogger
        >>> logger = FileLogger("/var/log/config.log")
        >>> manager = LinuxIniConfigManager(logger)
        >>> config = manager.read(Path("/etc/dnf/dnf.conf"))
        >>> print(config["main"]["fastestmirror"])
    """

    def __init__(self, logger: Logger) -> None:
        """Initialise le gestionnaire avec un logger.

        Args:
            logger: Instance de Logger pour les messages.
        """
        self.logger = logger

    def read(self, path: Path) -> dict[str, dict[str, str]]:
        """Lit un fichier INI et retourne son contenu.

        Args:
            path: Chemin du fichier INI.

        Returns:
            Dictionnaire imbriqué {section: {clé: valeur}}.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
        """
        if not path.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {path}")

        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")

        result: dict[str, dict[str, str]] = {}
        for section in parser.sections():
            result[section] = dict(parser[section])

        self.logger.log_info(f"Fichier {path} lu avec succès.")
        return result

    def write(self, path: Path, config: IniConfig) -> None:
        """Écrit une configuration dans un fichier INI.

        Args:
            path: Chemin du fichier de destination.
            config: Configuration à écrire.
        """
        parser = configparser.ConfigParser()

        for section in config.sections():
            parser[section.section_name()] = section.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            parser.write(f)

        self.logger.log_info(f"Fichier {path} écrit avec succès.")

    def write_section(self, path: Path, section: IniSection) -> None:
        """Écrit ou met à jour une section dans un fichier INI.

        Si le fichier existe, la section est mise à jour.
        Sinon, un nouveau fichier est créé.

        Args:
            path: Chemin du fichier INI.
            section: Section à écrire.
        """
        parser = configparser.ConfigParser()

        if path.exists():
            parser.read(path, encoding="utf-8")

        parser[section.section_name()] = section.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            parser.write(f)

        self.logger.log_info(
            f"Section [{section.section_name()}] écrite dans {path}."
        )

    def update_section(
        self,
        path: Path,
        section: IniSection,
        validators: dict[str, Any] | None = None,
    ) -> bool:
        """Met à jour une section dans un fichier INI existant.

        Compare les valeurs actuelles avec les nouvelles et n'écrit
        que si des modifications sont nécessaires.

        Args:
            path: Chemin du fichier INI.
            section: Section avec les nouvelles valeurs.
            validators: Validateurs optionnels (ignorés car la validation
                       est faite dans ValidatedSection).

        Returns:
            True si des modifications ont été effectuées, False sinon.
        """
        parser = configparser.ConfigParser()
        section_name = section.section_name()
        new_values = section.to_dict()

        if path.exists():
            parser.read(path, encoding="utf-8")

        if section_name not in parser:
            parser[section_name] = {}

        updated = False
        for key, new_value in new_values.items():
            current_value = parser[section_name].get(key)
            if current_value != new_value:
                parser[section_name][key] = new_value
                updated = True
                self.logger.log_info(
                    f"Modification : {key} mis à jour"
                )

        if updated:
            with open(path, "w", encoding="utf-8") as f:
                parser.write(f)
            self.logger.log_info(f"Fichier {path} mis à jour.")
        else:
            self.logger.log_info(
                f"Fichier {path} déjà configuré avec les valeurs cibles."
            )

        return updated

    def section_to_ini(self, section: IniSection) -> str:
        """Génère le contenu INI d'une section.

        Args:
            section: Section à convertir.

        Returns:
            Contenu INI formaté de la section.
        """
        parser = configparser.ConfigParser()
        parser[section.section_name()] = section.to_dict()

        output = StringIO()
        parser.write(output)
        return output.getvalue()

    def config_to_ini(self, config: IniConfig) -> str:
        """Génère le contenu INI d'une configuration complète.

        Args:
            config: Configuration à convertir.

        Returns:
            Contenu INI formaté complet.
        """
        parser = configparser.ConfigParser()

        for section in config.sections():
            parser[section.section_name()] = section.to_dict()

        output = StringIO()
        parser.write(output)
        return output.getvalue()
