"""Fonctions de chargement de configuration."""

import json
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Union


class ConfigLoader(ABC):
    """
    Interface abstraite pour le chargement de configuration.

    Permet l'injection de dépendance et facilite les tests
    en permettant de substituer l'implémentation réelle par un mock.
    """

    @abstractmethod
    def load(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Charge un fichier de configuration.

        Args:
            config_path: Chemin vers le fichier de configuration

        Returns:
            Dictionnaire de configuration

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le format n'est pas supporté
        """
        pass


class FileConfigLoader(ConfigLoader):
    """
    Implémentation du chargeur de configuration depuis fichiers.

    Supporte les formats TOML et JSON, détectés automatiquement
    par l'extension du fichier.
    """

    def load(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Charge un fichier de configuration TOML ou JSON.

        Le format est détecté automatiquement par l'extension du fichier.

        Args:
            config_path: Chemin vers le fichier de configuration

        Returns:
            Dictionnaire de configuration

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si l'extension n'est pas supportée
            tomllib.TOMLDecodeError: Si le TOML est invalide
            json.JSONDecodeError: Si le JSON est invalide
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Fichier de configuration non trouvé: {path}"
            )

        suffix = path.suffix.lower()

        if suffix == ".toml":
            with open(path, "rb") as f:
                return tomllib.load(f)
        elif suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(
                f"Extension non supportée: {suffix}. "
                "Utilisez .toml ou .json"
            )


# Instance par défaut pour rétrocompatibilité
_default_loader = FileConfigLoader()


def load_config(config_path: Union[str, Path]) -> dict:
    """
    Charge un fichier de configuration (fonction utilitaire).

    Utilise l'implémentation FileConfigLoader par défaut.
    Pour les tests ou une personnalisation, utiliser directement
    une instance de ConfigLoader.

    Args:
        config_path: Chemin vers le fichier de configuration

    Returns:
        Dictionnaire de configuration

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si l'extension n'est pas supportée
        tomllib.TOMLDecodeError: Si le TOML est invalide
        json.JSONDecodeError: Si le JSON est invalide
    """
    return _default_loader.load(config_path)
