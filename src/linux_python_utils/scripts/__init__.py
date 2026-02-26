"""
Module de génération et installation de scripts bash pour systèmes Linux.

Classes disponibles:
- BashScriptConfig: Configuration pour générer des scripts bash
  avec support optionnel des notifications.
- ScriptInstaller: Interface abstraite pour l'installation de scripts.
- BashScriptInstaller: Implémentation pour installer des scripts bash.
"""

from linux_python_utils.scripts.config import BashScriptConfig
from linux_python_utils.scripts.installer import (
    ScriptInstaller,
    BashScriptInstaller,
)

__all__ = [
    "BashScriptConfig",
    "ScriptInstaller",
    "BashScriptInstaller",
]
