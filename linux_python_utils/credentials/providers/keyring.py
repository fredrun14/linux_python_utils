"""Provider de credentials depuis le keyring systeme.

Ce module fournit KeyringCredentialProvider qui lit et ecrit
des credentials via le keyring FreeDesktop Secret Service.

Compatibilites :
- KWallet (KDE Plasma 6)
- KeePassXC (avec "Enable Secret Service" active)
- GNOME Keyring
"""

from typing import Any, Optional

from linux_python_utils.credentials.base import CredentialStore
from linux_python_utils.credentials.exceptions import (
    CredentialProviderUnavailableError,
    CredentialStoreError,
)
from linux_python_utils.logging.base import Logger


class KeyringCredentialProvider(CredentialStore):
    """Lit et ecrit des credentials via FreeDesktop Secret Service.

    Si le module keyring n'est pas installe, is_available() retourne
    False et les operations de lecture retournent None (degradation
    gracieuse). Les operations d'ecriture levent CredentialStoreError.

    Attributes:
        _logger: Logger optionnel.
        _backend: Backend keyring injecte (pour tests unitaires).
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        keyring_backend: Optional[Any] = None,
    ) -> None:
        """Initialise le provider keyring.

        Args:
            logger: Logger optionnel (injection de dependance).
            keyring_backend: Backend keyring optionnel. Permet
                d'injecter un mock pour les tests sans keyring
                systeme reel.
        """
        self._logger = logger
        self._backend = keyring_backend

    def _get_keyring(self) -> Any:
        """Retourne le module keyring ou le backend injecte.

        Returns:
            Module keyring ou backend de test.

        Raises:
            CredentialProviderUnavailableError: si keyring absent
                et aucun backend injecte.
        """
        if self._backend is not None:
            return self._backend
        try:
            import keyring
            return keyring
        except ImportError:
            raise CredentialProviderUnavailableError(
                "Le module 'keyring' n'est pas installe. "
                "Installez-le avec : pip install keyring"
            )

    def get(
        self,
        service: str,
        key: str,
    ) -> Optional[str]:
        """Lit un credential depuis le keyring systeme.

        Args:
            service: Nom du service applicatif.
            key: Identifiant de l'utilisateur ou de la cle.

        Returns:
            Valeur du credential ou None si absent ou indisponible.
        """
        if not self.is_available():
            return None
        try:
            kr = self._get_keyring()
            value = kr.get_password(service, key)
            return value if value else None
        except Exception:
            return None

    def set(
        self,
        service: str,
        key: str,
        value: str,
    ) -> None:
        """Stocke un credential dans le keyring systeme.

        Args:
            service: Nom du service applicatif.
            key: Identifiant de l'utilisateur ou de la cle.
            value: Valeur a stocker.

        Raises:
            CredentialStoreError: si le keyring est indisponible
                ou si l'operation echoue.
        """
        try:
            kr = self._get_keyring()
            kr.set_password(service, key, value)
            if self._logger:
                self._logger.log_info(
                    f"Credential stocke dans le keyring : "
                    f"service={service!r}, key={key!r}"
                )
        except CredentialProviderUnavailableError as exc:
            raise CredentialStoreError(str(exc)) from exc
        except Exception as exc:
            raise CredentialStoreError(
                f"Erreur lors du stockage keyring : {exc}"
            ) from exc

    def delete(
        self,
        service: str,
        key: str,
    ) -> None:
        """Supprime un credential du keyring systeme.

        Silencieux si le credential est absent.

        Args:
            service: Nom du service applicatif.
            key: Identifiant de l'utilisateur ou de la cle.
        """
        if not self.is_available():
            return
        try:
            kr = self._get_keyring()
            kr.delete_password(service, key)
            if self._logger:
                self._logger.log_info(
                    f"Credential supprime du keyring : "
                    f"service={service!r}, key={key!r}"
                )
        except Exception:
            pass

    def is_available(self) -> bool:
        """Indique si le keyring est operationnel.

        Returns:
            True si le module keyring est installe ou si un
            backend a ete injecte.
        """
        if self._backend is not None:
            return True
        try:
            import keyring  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def source_name(self) -> str:
        """Nom court de la source.

        Returns:
            "keyring"
        """
        return "keyring"
