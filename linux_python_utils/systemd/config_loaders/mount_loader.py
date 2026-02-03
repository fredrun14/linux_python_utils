"""Chargeur de configuration pour les unités .mount systemd.

Ce module fournit une classe pour charger un fichier TOML et créer
un MountConfig pour les unités systemd .mount.

Example:
    Chargement d'un MountConfig depuis un fichier TOML:

        loader = MountConfigLoader("config/mounts.toml")
        mount_config = loader.load()

    Fichier TOML attendu:

        [mount]
        description = "Partage NAS"
        what = "192.168.1.10:/share"
        where = "/media/nas"
        type = "nfs"
        options = "rw,soft"
"""

from pathlib import Path
from typing import Any

from linux_python_utils.config import ConfigLoader
from linux_python_utils.systemd import MountConfig
from linux_python_utils.systemd.config_loaders.base import TomlConfigLoader


class MountConfigLoader(TomlConfigLoader[MountConfig]):
    """Chargeur de configuration TOML pour MountConfig.

    Cette classe lit un fichier TOML et crée un MountConfig
    à partir de la section [mount].

    Attributes:
        DEFAULT_SECTION: Nom de la section par défaut ("mount").

    Example:
        >>> loader = MountConfigLoader("config/nas.toml")
        >>> config = loader.load()
        >>> print(config.where)
        /media/nas
    """

    DEFAULT_SECTION: str = "mount"

    def __init__(
        self,
        toml_path: str | Path,
        config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialise le loader pour MountConfig.

        Args:
            toml_path: Chemin vers le fichier de configuration TOML.
            config_loader: Chargeur de configuration injectable (DIP).

        Raises:
            FileNotFoundError: Si le fichier TOML n'existe pas.
            tomllib.TOMLDecodeError: Si le TOML est invalide.
        """
        super().__init__(toml_path, config_loader)

    def load(self, section: str | None = None) -> MountConfig:
        """Charge et retourne un MountConfig.

        Args:
            section: Nom de la section à charger.
                Par défaut "mount".

        Returns:
            Instance de MountConfig avec les valeurs du TOML.

        Raises:
            KeyError: Si la section n'existe pas.
            TypeError: Si les champs requis sont manquants.
            ValueError: Si 'what' ou 'where' sont vides.

        Example:
            >>> loader = MountConfigLoader("config/nas.toml")
            >>> config = loader.load()
            >>> config.type
            'nfs'
        """
        section_name = section or self.DEFAULT_SECTION
        data: dict[str, Any] = self._get_section(section_name)

        return MountConfig(
            description=data["description"],
            what=data["what"],
            where=data["where"],
            type=data["type"],
            options=data.get("options", ""),
        )

    def load_multiple(self, section: str | None = None) -> list[MountConfig]:
        """Charge plusieurs MountConfig depuis une section de liste.

        Permet de définir plusieurs montages dans un seul fichier TOML
        sous forme de liste.

        Args:
            section: Nom de la section contenant la liste.
                Par défaut "mounts" (pluriel).

        Returns:
            Liste d'instances de MountConfig.

        Raises:
            KeyError: Si la section n'existe pas.
            TypeError: Si la section n'est pas une liste.

        Example:
            Fichier TOML:

                [[mounts]]
                description = "NAS principal"
                what = "192.168.1.10:/share"
                where = "/media/nas"
                type = "nfs"

                [[mounts]]
                description = "NAS backup"
                what = "192.168.1.11:/backup"
                where = "/media/backup"
                type = "nfs"

            >>> loader = MountConfigLoader("config/mounts.toml")
            >>> configs = loader.load_multiple("mounts")
            >>> len(configs)
            2
        """
        section_name = section or "mounts"
        data = self._get_section(section_name)

        if not isinstance(data, list):
            raise TypeError(
                f"La section '{section_name}' doit être une liste "
                "(utilisez [[{section_name}]] dans le TOML)"
            )

        return [
            MountConfig(
                description=item["description"],
                what=item["what"],
                where=item["where"],
                type=item["type"],
                options=item.get("options", ""),
            )
            for item in data
        ]
