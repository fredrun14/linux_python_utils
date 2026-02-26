"""Gestion des sauvegardes de fichiers."""

import shutil
import os
from abc import ABC, abstractmethod

from linux_python_utils.logging.base import Logger


class FileBackup(ABC):
    """Interface pour la gestion des sauvegardes de fichiers."""

    @abstractmethod
    def backup(self, file_path: str, backup_path: str) -> None:
        """
        Crée une sauvegarde d'un fichier.

        Args:
            file_path: Chemin du fichier à sauvegarder
            backup_path: Chemin de la sauvegarde
        """
        pass

    @abstractmethod
    def restore(self, file_path: str, backup_path: str) -> None:
        """
        Restaure un fichier depuis sa sauvegarde.

        Args:
            file_path: Chemin du fichier à restaurer
            backup_path: Chemin de la sauvegarde
        """
        pass


class LinuxFileBackup(FileBackup):
    """
    Implémentation Linux de la sauvegarde de fichiers.

    Utilise shutil.copy2 pour préserver les métadonnées
    (permissions, timestamps) lors de la copie.
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialise le gestionnaire de sauvegarde.

        Args:
            logger: Instance de Logger pour le logging
        """
        self.logger = logger

    def backup(self, file_path: str, backup_path: str) -> None:
        """
        Crée une sauvegarde d'un fichier.

        Args:
            file_path: Chemin du fichier à sauvegarder
            backup_path: Chemin de la sauvegarde

        Raises:
            Exception: Si la sauvegarde échoue
        """
        try:
            if os.path.exists(file_path):
                shutil.copy2(file_path, backup_path)
                self.logger.log_info(
                    f"Sauvegarde de {file_path} vers {backup_path}"
                )
            else:
                self.logger.log_warning(
                    f"Le fichier {file_path} n'existe pas. "
                    "Création d'un nouveau fichier."
                )
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la sauvegarde de {file_path}: {e}"
            )
            raise

    def restore(self, file_path: str, backup_path: str) -> None:
        """
        Restaure un fichier depuis sa sauvegarde.

        Args:
            file_path: Chemin du fichier à restaurer
            backup_path: Chemin de la sauvegarde

        Raises:
            FileNotFoundError: Si la sauvegarde n'existe pas
            Exception: Si la restauration échoue
        """
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                self.logger.log_info(
                    f"Restauration de {file_path} depuis {backup_path}"
                )
            else:
                error_msg = f"Aucune sauvegarde disponible: {backup_path}"
                self.logger.log_error(error_msg)
                raise FileNotFoundError(error_msg)
        except FileNotFoundError:
            raise
        except Exception as e:
            self.logger.log_error(
                f"Erreur lors de la restauration de {file_path}: {e}"
            )
            raise
