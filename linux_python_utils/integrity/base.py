"""Interface abstraite et utilitaires pour la vérification d'intégrité."""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union


class ChecksumCalculator(ABC):
    """
    Interface abstraite pour le calcul de checksums.

    Permet l'injection de dépendance et facilite les tests
    en permettant de substituer l'implémentation réelle par un mock.
    """

    @abstractmethod
    def calculate(
        self,
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
        pass


class HashLibChecksumCalculator(ChecksumCalculator):
    """
    Implémentation du calculateur de checksum utilisant hashlib.

    Supporte tous les algorithmes disponibles dans hashlib
    (sha256, sha512, md5, sha1, etc.).
    """

    def calculate(
        self,
        file_path: Union[str, Path],
        algorithm: str = 'sha256'
    ) -> str:
        """
        Calcule le checksum d'un fichier avec hashlib.

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


# Instance par défaut pour rétrocompatibilité
_default_calculator = HashLibChecksumCalculator()


def calculate_checksum(
    file_path: Union[str, Path],
    algorithm: str = 'sha256'
) -> str:
    """
    Calcule le checksum d'un fichier (fonction utilitaire).

    Utilise l'implémentation HashLibChecksumCalculator par défaut.
    Pour les tests ou une personnalisation, utiliser directement
    une instance de ChecksumCalculator.

    Args:
        file_path: Chemin du fichier
        algorithm: Algorithme de hash (sha256, sha512, md5, etc.)

    Returns:
        Checksum hexadécimal du fichier

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si l'algorithme n'est pas supporté
    """
    return _default_calculator.calculate(file_path, algorithm)


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
