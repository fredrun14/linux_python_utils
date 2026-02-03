"""Classe de base abstraite pour les chargeurs de configuration systemd.

Ce module définit l'interface commune pour tous les chargeurs de
configuration TOML vers dataclasses systemd.

Example:
    Création d'un loader personnalisé:

        class MyConfigLoader(TomlConfigLoader[MyConfig]):
            def load(self, section: str = "my_section") -> MyConfig:
                data = self._get_section(section)
                return MyConfig(**data)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from linux_python_utils.config import ConfigLoader, FileConfigLoader

# Type générique pour la dataclass de configuration
T = TypeVar("T")


class TomlConfigLoader(ABC, Generic[T]):
    """Classe de base abstraite pour les chargeurs de configuration TOML.

    Cette classe fournit l'infrastructure commune pour charger un fichier
    TOML et extraire une section spécifique pour créer une dataclass.

    Attributes:
        _config: Dictionnaire de configuration chargé depuis le fichier TOML.

    Example:
        >>> class ServiceLoader(TomlConfigLoader[ServiceConfig]):
        ...     def load(self, section: str = "service") -> ServiceConfig:
        ...         data = self._get_section(section)
        ...         return ServiceConfig(**data)
    """

    def __init__(
        self,
        toml_path: str | Path,
        config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialise le loader en chargeant le fichier TOML.

        Args:
            toml_path: Chemin vers le fichier de configuration TOML.
            config_loader: Chargeur de configuration injectable (DIP).
                Si None, utilise FileConfigLoader par défaut.

        Raises:
            FileNotFoundError: Si le fichier TOML n'existe pas.
            tomllib.TOMLDecodeError: Si le TOML est invalide.
        """
        loader = config_loader or FileConfigLoader()
        self._config: dict[str, Any] = loader.load(toml_path)

    @property
    def config(self) -> dict[str, Any]:
        """Retourne le dictionnaire de configuration brut.

        Returns:
            Dictionnaire complet de la configuration TOML.
        """
        return self._config

    def _get_section(self, section: str) -> dict[str, Any]:
        """Extrait une section du fichier de configuration.

        Args:
            section: Nom de la section à extraire (ex: "service", "timer").

        Returns:
            Dictionnaire contenant les données de la section.

        Raises:
            KeyError: Si la section n'existe pas dans le fichier TOML.
        """
        if section not in self._config:
            available = list(self._config.keys())
            raise KeyError(
                f"Section '{section}' non trouvée dans le fichier TOML. "
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
