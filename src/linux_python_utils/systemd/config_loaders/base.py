"""Classe de base abstraite pour les chargeurs de configuration systemd.

Ce module définit l'interface commune pour tous les chargeurs de
configuration (TOML, JSON) vers dataclasses systemd.

Example:
    Création d'un loader personnalisé:

        class MyConfigLoader(ConfigFileLoader[MyConfig]):
            def load(self, section: str = "my_section") -> MyConfig:
                data = self._get_section(section)
                return MyConfig(**data)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar
import warnings

from linux_python_utils.config import ConfigLoader, FileConfigLoader

#
# # Alias pour rétrocompatibilité (deprecated)
# class TomlConfigLoader(ConfigFileLoader[T]):
#     """Alias deprecated pour ConfigFileLoader.
#
#     .. deprecated::
#         Utilisez ConfigFileLoader à la place.
#     """
#
#     def __init__(
#         self,
#         toml_path: str | Path,
#         config_loader: ConfigLoader | None = None
#     ) -> None:
#         """Initialise le loader (deprecated).
#
#         Args:
#             toml_path: Chemin vers le fichier de configuration.
#             config_loader: Chargeur de configuration injectable.
#         """
#         warnings.warn(
#             "TomlConfigLoader est deprecated, utilisez ConfigFileLoader",
#             DeprecationWarning,
#             stacklevel=2
#         )
#         super().__init__(toml_path, config_loader)
#
#     @abstractmethod
#     def load(self, section: str | None = None) -> T:
#         """Charge et retourne la dataclass de configuration."""
#         pass
