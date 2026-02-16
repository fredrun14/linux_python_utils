"""Vérificateur d'intégrité SHA256 pour fichiers et répertoires."""

import os
from pathlib import Path
from typing import Optional

from linux_python_utils.logging.base import Logger
from linux_python_utils.integrity.base import (
    IntegrityChecker,
    ChecksumCalculator,
    HashLibChecksumCalculator,
    calculate_checksum
)


class SHA256IntegrityChecker(IntegrityChecker):
    """Vérificateur d'intégrité basé sur SHA256.

    Compare les checksums entre source et destination pour vérifier
    que les fichiers ont été copiés correctement.

    Respecte le principe DIP en acceptant un ChecksumCalculator
    en injection de dépendance, facilitant les tests unitaires.
    """

    def __init__(
        self,
        logger: Logger,
        algorithm: str = 'sha256',
        checksum_calculator: Optional[ChecksumCalculator] = None
    ) -> None:
        """Initialise le vérificateur d'intégrité.

        Args:
            logger: Instance de Logger pour le logging.
            algorithm: Algorithme de hash (défaut: sha256).
            checksum_calculator: Instance de ChecksumCalculator (optionnel).
                Si non fourni, utilise HashLibChecksumCalculator par défaut.
        """
        self.logger = logger
        self.algorithm = algorithm
        self._calculator = checksum_calculator or HashLibChecksumCalculator()

    @staticmethod
    def calculate_checksum(
        file_path: str,
        algorithm: str = 'sha256'
    ) -> str:
        """Calcule le checksum d'un fichier (méthode statique).

        Args:
            file_path: Chemin du fichier.
            algorithm: Algorithme de hash (défaut: sha256).

        Returns:
            Checksum hexadécimal du fichier.
        """
        return calculate_checksum(file_path, algorithm)

    def _calculate(self, file_path: str) -> str:
        """Calcule le checksum via l'instance injectée.

        Args:
            file_path: Chemin du fichier.

        Returns:
            Checksum hexadécimal du fichier.
        """
        return self._calculator.calculate(file_path, self.algorithm)

    def verify_file(
        self,
        source_file: str,
        dest_file: str
    ) -> bool:
        """
        Vérifie l'intégrité d'un fichier unique.

        Args:
            source_file: Chemin du fichier source
            dest_file: Chemin du fichier destination

        Returns:
            True si les checksums correspondent, False sinon
        """
        try:
            source_checksum = self._calculate(source_file)
            dest_checksum = self._calculate(dest_file)

            if source_checksum != dest_checksum:
                self.logger.log_error(
                    f"Différence de checksum:\n"
                    f"  Source: {source_checksum}\n"
                    f"  Dest:   {dest_checksum}"
                )
                return False
            return True
        except OSError as e:
            self.logger.log_error(f"Erreur de vérification: {e}")
            return False

    def verify(
        self,
        source: str,
        destination: str,
        dest_subdir: Optional[str] = None
    ) -> bool:
        """
        Vérifie l'intégrité d'une copie de répertoire.

        Gère automatiquement le cas où rsync crée un sous-répertoire
        avec le nom du source dans la destination.

        Args:
            source: Chemin du répertoire source
            destination: Chemin du répertoire destination
            dest_subdir: Sous-répertoire optionnel dans destination

        Returns:
            True si tous les fichiers correspondent, False sinon
        """
        try:
            source = Path(source)
            destination = Path(destination)

            # Déterminer le répertoire de destination effectif
            if dest_subdir:
                actual_dest = destination / dest_subdir
            else:
                # rsync copie source/ vers destination/basename(source)/
                source_name = source.name
                actual_dest = destination / source_name
                if not actual_dest.exists():
                    actual_dest = destination

            self.logger.log_info(
                f"Vérification: {source} -> {actual_dest}"
            )

            # Parcourir les fichiers source
            for root, _, files in os.walk(str(source)):
                for file in files:
                    source_file = Path(root) / file

                    # Chemin relatif par rapport au source
                    rel_path = source_file.relative_to(source)

                    # Fichier destination correspondant
                    dest_file = actual_dest / rel_path

                    if not dest_file.exists():
                        self.logger.log_error(
                            f"Fichier manquant: {dest_file}"
                        )
                        return False

                    if not self.verify_file(str(source_file), str(dest_file)):
                        self.logger.log_error(
                            f"Checksum différent pour: {rel_path}"
                        )
                        return False

            self.logger.log_info(
                "Tous les fichiers ont été vérifiés avec succès."
            )
            return True

        except OSError as e:
            self.logger.log_error(
                f"Erreur lors de la vérification d'intégrité: {e}"
            )
            return False

    def get_checksum(self, file_path: str) -> str:
        """
        Calcule et retourne le checksum d'un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            Checksum hexadécimal
        """
        checksum = self._calculate(file_path)
        self.logger.log_info(f"Checksum de {file_path}: {checksum}")
        return checksum
