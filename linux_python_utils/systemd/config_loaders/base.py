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

# Type générique pour la dataclass de configuration
T = TypeVar("T")


class ConfigFileLoader(ABC, Generic[T]):
    """Classe de base abstraite pour les chargeurs de configuration.

    Cette classe fournit l'infrastructure commune pour charger un fichier
    de configuration (TOML ou JSON) et extraire une section spécifique
    pour créer une dataclass.

    Le format est automatiquement détecté par l'extension du fichier:
    - .toml : Format TOML
    - .json : Format JSON

    Attributes:
        _config: Dictionnaire de configuration chargé depuis le fichier.

    Example:
        >>> class ServiceLoader(ConfigFileLoader[ServiceConfig]):
        ...     def load(self, section: str = "service") -> ServiceConfig:
        ...         data = self._get_section(section)
        ...         return ServiceConfig(**data)
    """

    def __init__(
        self,
        config_path: str | Path,
        config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialise le loader en chargeant le fichier de configuration.

        Args:
            config_path: Chemin vers le fichier de configuration (.toml ou .json).
            config_loader: Chargeur de configuration injectable (DIP).
                Si None, utilise FileConfigLoader par défaut.

        Raises:
            FileNotFoundError: Si le fichier de configuration n'existe pas.
            ValueError: Si l'extension du fichier n'est pas supportée.
            tomllib.TOMLDecodeError: Si le TOML est invalide.
            json.JSONDecodeError: Si le JSON est invalide.
        """
        loader = config_loader or FileConfigLoader()
        self._config: dict[str, Any] = loader.load(config_path)

    @property
    def config(self) -> dict[str, Any]:
        """Retourne le dictionnaire de configuration brut.

        Returns:
            Dictionnaire complet de la configuration.
        """
        return self._config

    def _get_section(self, section: str) -> dict[str, Any]:
        """Extrait une section du fichier de configuration.

        Args:
            section: Nom de la section à extraire (ex: "service", "timer").

        Returns:
            Dictionnaire contenant les données de la section.

        Raises:
            KeyError: Si la section n'existe pas dans le fichier.
        """
        if section not in self._config:
            available = list(self._config.keys())
            raise KeyError(
                f"Section '{section}' non trouvée dans le fichier. "
                f"Sections disponibles: {available}"
            )
        return self._config[section]

    def _get_nested_value(
        self,
        *keys: str,
        default: Any = None
    ) -> Any:
        """Extrait une valeur imbriquée du fichier de configuration.

        Args:
            *keys: Clés successives pour naviguer dans la structure.
            default: Valeur par défaut si le chemin n'existe pas.

        Returns:
            Valeur trouvée ou default si non trouvée.

        Example:
            >>> loader._get_nested_value("paths", "log_file")
        """
        current = self._config
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    @abstractmethod
    def load(self, section: str | None = None) -> T:
        """Charge et retourne la dataclass de configuration.

        Args:
            section: Nom de la section à charger. Si None, utilise
                la section par défaut du loader.

        Returns:
            Instance de la dataclass de configuration.

        Raises:
            KeyError: Si la section requise n'existe pas.
            TypeError: Si les données ne correspondent pas à la dataclass.
        """
        pass


# Alias pour rétrocompatibilité (deprecated)
class TomlConfigLoader(ConfigFileLoader[T]):
    """Alias deprecated pour ConfigFileLoader.

    .. deprecated::
        Utilisez ConfigFileLoader à la place.
    """

    def __init__(
        self,
        toml_path: str | Path,
        config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialise le loader (deprecated).

        Args:
            toml_path: Chemin vers le fichier de configuration.
            config_loader: Chargeur de configuration injectable.
        """
        warnings.warn(
            "TomlConfigLoader est deprecated, utilisez ConfigFileLoader",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(toml_path, config_loader)

    @abstractmethod
    def load(self, section: str | None = None) -> T:
        """Charge et retourne la dataclass de configuration."""
        pass
