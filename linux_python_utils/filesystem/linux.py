"""Implémentation Linux de la gestion des fichiers."""

from pathlib import Path

from linux_python_utils.logging.base import Logger
from linux_python_utils.filesystem.base import FileManager


class LinuxFileManager(FileManager):
    """
    Implémentation Linux de la gestion des fichiers.

    Toutes les opérations sont loggées via l'instance Logger.
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialise le gestionnaire de fichiers.

        Args:
            logger: Instance de Logger pour le logging
        """
        self.logger = logger

    def create_file(self, file_path: str, content: str) -> bool:
        """
        Crée un fichier avec le contenu spécifié.

        Args:
            file_path: Chemin du fichier à créer
            content: Contenu du fichier

        Returns:
            True si succès, False sinon
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.log_info(f"Fichier {file_path} créé avec succès.")
            return True
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la création du fichier {file_path}: {e}"
            )
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        Vérifie si un fichier existe.

        Args:
            file_path: Chemin du fichier

        Returns:
            True si le fichier existe, False sinon
        """
        return Path(file_path).exists()

    def read_file(self, file_path: str) -> str:
        """
        Lit le contenu d'un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            Contenu du fichier

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.log_info(f"Fichier {file_path} lu avec succès.")
            return content
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la lecture du fichier {file_path}: {e}"
            )
            raise

    def delete_file(self, file_path: str) -> bool:
        """
        Supprime un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            True si succès, False sinon
        """
        try:
            Path(file_path).unlink()
            self.logger.log_info(f"Fichier {file_path} supprimé avec succès.")
            return True
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la suppression du fichier {file_path}: {e}"
            )
            return False
