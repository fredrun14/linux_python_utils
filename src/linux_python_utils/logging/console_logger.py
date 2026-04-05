"""Logger console sans effet de bord fichier.

Implémente l'interface Logger en écrivant uniquement sur stdout/stderr.
Adapté aux contextes légers : dry-run, scripts sans log fichier, tests.
"""

import sys

from linux_python_utils.logging.base import Logger


class ConsoleLogger(Logger):
    """Logger écrivant sur stdout/stderr sans fichier de log.

    Les messages d'information sont écrits sur stdout.
    Les avertissements et erreurs sont écrits sur stderr.
    Aucun fichier n'est créé ou modifié.

    Example:
        >>> logger = ConsoleLogger()
        >>> logger.log_info("Démarrage...")
        Démarrage...
        >>> logger.log_warning("Fichier absent")
        WARNING: Fichier absent
    """

    def log_info(self, message: str) -> None:
        """Écrit un message d'information sur stdout.

        Args:
            message: Message à afficher.
        """
        print(message)

    def log_warning(self, message: str) -> None:
        """Écrit un avertissement sur stderr.

        Args:
            message: Message à afficher.
        """
        print(f"WARNING: {message}", file=sys.stderr)

    def log_error(self, message: str) -> None:
        """Écrit une erreur sur stderr.

        Args:
            message: Message à afficher.
        """
        print(f"ERROR: {message}", file=sys.stderr)
