"""Interface abstraite pour la validation."""

from abc import ABC, abstractmethod


class Validator(ABC):
    """
    Interface abstraite pour les validateurs.

    Permet l'injection de dépendance et facilite les tests
    en permettant de substituer l'implémentation réelle par un mock.
    """

    @abstractmethod
    def validate(self) -> None:
        """
        Exécute la validation.

        Raises:
            ValueError: Si une valeur est invalide
            PermissionError: Si les permissions sont insuffisantes
            Exception: Selon l'implémentation concrète
        """
        pass
