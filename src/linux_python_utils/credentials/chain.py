"""Chaine de priorite de providers de credentials.

Ce module implemente le pattern Chain of Responsibility pour
parcourir une liste ordonnee de providers jusqu'a trouver
un credential.
"""

from pathlib import Path
from typing import List, Optional, Union

from linux_python_utils.credentials.base import CredentialProvider
from linux_python_utils.credentials.models import Credential
from linux_python_utils.credentials.providers.dotenv import (
    DotEnvCredentialProvider,
)
from linux_python_utils.credentials.providers.env import (
    EnvCredentialProvider,
)
from linux_python_utils.credentials.providers.keyring import (
    KeyringCredentialProvider,
)
from linux_python_utils.logging.base import Logger


class CredentialChain(CredentialProvider):
    """Parcourt une liste ordonnee de providers jusqu'au premier succes.

    Exemple de chaine pour scanNetHome :

        chain = CredentialChain([
            EnvCredentialProvider(),
            DotEnvCredentialProvider(path),
            KeyringCredentialProvider(),
        ])
        password = chain.get("scannethome", "ASUS_ROUTER_PASSWORD") or ""

    Attributes:
        _providers: Liste ordonnee de providers (priorite decroissante).
        _logger: Logger optionnel.
    """

    def __init__(
        self,
        providers: List[CredentialProvider],
        logger: Optional[Logger] = None,
    ) -> None:
        """Initialise la chaine de providers.

        Args:
            providers: Liste ordonnee de providers.
            logger: Logger optionnel (injection de dependance).
        """
        self._providers = providers
        self._logger = logger

    def get(
        self,
        service: str,
        key: str,
    ) -> Optional[str]:
        """Retourne le premier credential trouve dans la chaine.

        Les providers indisponibles (is_available() == False)
        sont ignores silencieusement.

        Args:
            service: Nom du service applicatif.
            key: Nom de la cle.

        Returns:
            Valeur du credential ou None si absent de tous les
            providers.
        """
        for provider in self._providers:
            if not provider.is_available():
                continue
            value = provider.get(service, key)
            if value:
                if self._logger:
                    self._logger.log_info(
                        f"Credential trouve via "
                        f"{provider.source_name!r} : "
                        f"service={service!r}, key={key!r}"
                    )
                return value
            if self._logger:
                self._logger.log_info(
                    f"Credential absent de "
                    f"{provider.source_name!r} : "
                    f"service={service!r}, "
                    f"key={key!r} — escalade"
                )
        return None

    def get_with_source(
        self,
        service: str,
        key: str,
    ) -> Optional[Credential]:
        """Retourne le credential avec la source d'origine.

        Args:
            service: Nom du service applicatif.
            key: Nom de la cle.

        Returns:
            Instance de Credential avec source renseignee,
            ou None si absent de tous les providers.
        """
        for provider in self._providers:
            if not provider.is_available():
                continue
            value = provider.get(service, key)
            if value:
                return Credential(
                    service=service,
                    key=key,
                    value=value,
                    source=provider.source_name,
                )
        return None

    def is_available(self) -> bool:
        """Indique si au moins un provider est disponible.

        Returns:
            True si au moins un provider est operationnel.
        """
        return any(
            p.is_available() for p in self._providers
        )

    @property
    def source_name(self) -> str:
        """Nom court de la source.

        Returns:
            "chain"
        """
        return "chain"

    @classmethod
    def default(
        cls,
        dotenv_path: Optional[Union[str, Path]] = None,
        logger: Optional[Logger] = None,
    ) -> "CredentialChain":
        """Cree la chaine standard env -> dotenv -> keyring.

        Args:
            dotenv_path: Chemin optionnel vers un fichier .env.
                Si None, le provider dotenv est omis de la chaine.
            logger: Logger optionnel partage entre les providers.

        Returns:
            Instance de CredentialChain avec les providers
            standards dans l'ordre de priorite.
        """
        providers: List[CredentialProvider] = [
            EnvCredentialProvider(logger=logger),
        ]
        if dotenv_path is not None:
            providers.append(
                DotEnvCredentialProvider(
                    dotenv_path=dotenv_path,
                    logger=logger,
                )
            )
        providers.append(
            KeyringCredentialProvider(logger=logger)
        )
        return cls(providers=providers, logger=logger)
