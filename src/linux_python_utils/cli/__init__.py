"""Framework CLI basé sur le Command Pattern.

Provides:
    CliCommand: Interface abstraite pour une sous-commande.
    CliApplication: Orchestrateur CLI.
"""

from linux_python_utils.cli.base import CliApplication, CliCommand

__all__ = ["CliCommand", "CliApplication"]
