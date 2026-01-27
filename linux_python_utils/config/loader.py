"""Fonctions de chargement de configuration."""

import json
import tomllib
from pathlib import Path
from typing import Union


def load_config(config_path: Union[str, Path]) -> dict:
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
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {path}")

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
