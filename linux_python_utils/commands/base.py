"""Interfaces abstraites et structures de données pour l'exécution
de commandes système.

Ce module définit :
    - CommandResult : Résultat immuable d'une exécution de commande.
    - CommandExecutor : Interface abstraite pour les exécuteurs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CommandResult:
    """Résultat de l'exécution d'une commande système.

    Attributes:
        command: Commande exécutée sous forme de liste.
        return_code: Code de retour du processus.
        stdout: Sortie standard capturée.
        stderr: Sortie d'erreur capturée.
        success: True si la commande a réussi (code 0).
        duration: Durée d'exécution en secondes.
    """

    command: List[str]
    return_code: int
    stdout: str
    stderr: str
    success: bool
    duration: float


class CommandExecutor(ABC):
    """Interface abstraite pour l'exécution de commandes système."""

    @abstractmethod
    def run(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """Exécute une commande et retourne le résultat.

        Args:
            command: Commande sous forme de liste.
            env: Variables d'environnement supplémentaires.
            cwd: Répertoire de travail.
            timeout: Timeout en secondes.

        Returns:
            Résultat de l'exécution.
        """
        pass

    @abstractmethod
    def run_streaming(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """Exécute une commande avec sortie en temps réel.

        Args:
            command: Commande sous forme de liste.
            env: Variables d'environnement supplémentaires.
            cwd: Répertoire de travail.
            timeout: Timeout en secondes.

        Returns:
            Résultat de l'exécution.
        """
        pass
