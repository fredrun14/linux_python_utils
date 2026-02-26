"""Validateur de sécurité pour fichiers world-writable."""

import stat
from pathlib import Path
from typing import Union

from linux_python_utils.validation.base import Validator


class PathCheckerWorldWritable(Validator):
    """Vérifie qu'un fichier n'est pas accessible en écriture par tous.

    Essentiel pour tout script exécuté en root chargeant un fichier
    de configuration : un fichier world-writable pourrait être modifié
    par un utilisateur non-privilégié (élévation de privilèges).

    Lève des exceptions standard (FileNotFoundError, PermissionError)
    pour rester générique. Le consommateur peut les wrapper vers ses
    propres exceptions métier.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Initialise le validateur avec le chemin du fichier à vérifier.

        Args:
            path: Chemin vers le fichier dont vérifier les permissions.
        """
        self._path = Path(path).resolve()

    def validate(self) -> None:
        """Vérifie que le fichier n'est pas world-writable.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            PermissionError: Si le fichier est modifiable par tous
                les utilisateurs (bit S_IWOTH positionné).
        """
        if not self._path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {self._path}")

        file_stat = self._path.stat()
        if file_stat.st_mode & stat.S_IWOTH:
            raise PermissionError(
                f"Le fichier {self._path} est modifiable par tous "
                f"les utilisateurs (world-writable). "
                f"Corrigez avec : chmod o-w {self._path}"
            )
