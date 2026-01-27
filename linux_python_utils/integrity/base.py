"""Interface abstraite et utilitaires pour la vérification d'intégrité."""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union


def calculate_checksum(
    file_path: Union[str, Path],
    algorithm: str = 'sha256'
) -> str:
    """
    Calcule le checksum d'un fichier.

    Args:
        file_path: Chemin du fichier
        algorithm: Algorithme de hash (sha256, sha512, md5, etc.)

    Returns:
        Checksum hexadécimal du fichier

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si l'algorithme n'est pas supporté
    """
    try:
        hash_func = getattr(hashlib, algorithm)()
    except AttributeError:
        raise ValueError(f"Algorithme non supporté: {algorithm}")

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


class IntegrityChecker(ABC):
    """Interface pour la vérification d'intégrité."""

    @abstractmethod
    def verify(self, source: str, destination: str) -> bool:
        """
        Vérifie l'intégrité entre source et destination.

        Args:
            source: Chemin source
            destination: Chemin destination

        Returns:
            True si l'intégrité est vérifiée, False sinon
        """
        pass
