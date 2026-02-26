"""Module d'exécution de commandes système.

Ce module fournit des classes pour construire et exécuter
des commandes système de manière structurée.

Classes disponibles :
    CommandResult : Résultat immuable d'une exécution.
    CommandExecutor : Interface abstraite pour les exécuteurs.
    CommandBuilder : Constructeur fluent de commandes.
    LinuxCommandExecutor : Exécuteur concret via subprocess.
    CommandFormatter : Interface abstraite de formatage.
    PlainCommandFormatter : Formatage texte brut (logs fichier).
    AnsiCommandFormatter : Formatage ANSI coloré (console).
"""

from linux_python_utils.commands.base import (
    CommandResult,
    CommandExecutor,
)
from linux_python_utils.commands.builder import CommandBuilder
from linux_python_utils.commands.formatter import (
    CommandFormatter,
    PlainCommandFormatter,
    AnsiCommandFormatter,
)
from linux_python_utils.commands.runner import (
    LinuxCommandExecutor,
)

__all__ = [
    # Structures de données
    "CommandResult",
    # Interface abstraite
    "CommandExecutor",
    # Constructeur
    "CommandBuilder",
    # Formateurs
    "CommandFormatter",
    "PlainCommandFormatter",
    "AnsiCommandFormatter",
    # Implémentation Linux
    "LinuxCommandExecutor",
]
