"""Interfaces abstraites pour la gestion des credentials.

Ce module definit les ABCs CredentialProvider (lecture seule)
et CredentialStore (lecture + ecriture) selon le principe ISP
(Interface Segregation Principle).
"""

from abc import ABC, abstractmethod
from typing import Optional


class CredentialProvider(ABC):
    """Interface de lecture d'un credential depuis une source."""

    @abstractmethod
    def get(
        self,
        service: str,
        key: str,
    ) -> Optional[str]:
        """Retourne la valeur du credential ou None si absent.

        Args:
            service: Nom du service applicatif.
            key: Nom de la cle.

        Returns:
            Valeur du credential ou None si absent.
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_available(self) -> bool:
        """Indique si ce provider est operationnel.

        Returns:
            True si le provider peut etre utilise.
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Nom court de la source.

        Returns:
            Nom de la source (ex: "env", "dotenv", "keyring").
        """
        pass  # pragma: no cover


class CredentialStore(CredentialProvider):
    """Interface de lecture et d'ecriture d'un credential.

    Etend CredentialProvider avec les operations d'ecriture.
    Les clients qui lisent seulement doivent dependre de
    CredentialProvider, pas de CredentialStore (ISP).
    """

    @abstractmethod
    def set(
        self,
        service: str,
        key: str,
        value: str,
    ) -> None:
        """Stocke un credential.

        Args:
            service: Nom du service applicatif.
            key: Nom de la cle.
            value: Valeur a stocker.

        Raises:
            CredentialStoreError: si le stockage echoue.
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete(
        self,
        service: str,
        key: str,
    ) -> None:
        """Supprime un credential.

        Doit etre silencieux si le credential est absent.

        Args:
            service: Nom du service applicatif.
            key: Nom de la cle.
        """
        pass  # pragma: no cover
