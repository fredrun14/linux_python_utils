"""Validateur de chemins de fichiers."""

import os

from linux_python_utils.validation.base import Validator


class PathChecker(Validator):
    """
    Vérifie que les répertoires parents des chemins existent
    et sont accessibles en écriture.

    Lève des exceptions standard (ValueError, PermissionError)
    pour rester générique. Le consommateur peut les wrapper
    vers ses propres exceptions métier.
    """

    def __init__(self, paths: list[str]):
        """
        Initialise le validateur avec une liste de chemins.

        Args:
            paths: Liste de chemins de fichiers à valider
        """
        self.paths = paths

    def validate(self) -> None:
        """
        Valide que tous les répertoires parents existent
        et sont accessibles en écriture.

        Raises:
            ValueError: Si un répertoire parent n'existe pas
            PermissionError: Si un répertoire parent n'est pas
                accessible en écriture
        """
        for path in self.paths:
            self._validate_path(path)

    def _validate_path(self, path: str) -> None:
        """
        Valide un chemin spécifique.

        Args:
            path: Chemin du fichier à valider
        """
        dirname = os.path.dirname(path)

        if not os.path.exists(dirname):
            raise ValueError(
                f"Le répertoire {dirname} n'existe pas."
            )

        if not os.access(dirname, os.W_OK):
            raise PermissionError(
                f"Permissions insuffisantes pour écrire dans {dirname}."
            )
