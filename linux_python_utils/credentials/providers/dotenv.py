"""Provider de credentials depuis un fichier .env.

Ce module fournit DotEnvCredentialProvider qui charge un fichier
.env via python-dotenv (dependance optionnelle) puis lit les
credentials depuis os.environ.
"""

import os
from pathlib import Path
from typing import Optional, Union

from linux_python_utils.credentials.base import CredentialProvider
from linux_python_utils.logging.base import Logger


class DotEnvCredentialProvider(CredentialProvider):
    """Charge un fichier .env puis lit les credentials via os.environ.

    Utilise python-dotenv avec override=False : les variables shell
    existantes ont priorite sur le contenu du fichier .env.

    Si python-dotenv n'est pas installe, is_available() retourne
    False et get() retourne toujours None (degradation gracieuse).

    Attributes:
        _dotenv_path: Chemin vers le fichier .env.
        _logger: Logger optionnel.
        _loaded: True si le fichier a ete charge avec succes.
    """

    def __init__(
        self,
        dotenv_path: Union[str, Path],
        logger: Optional[Logger] = None,
    ) -> None:
        """Initialise le provider de fichier .env.

        Args:
            dotenv_path: Chemin vers le fichier .env.
            logger: Logger optionnel (injection de dependance).
        """
        self._dotenv_path = Path(dotenv_path)
        self._logger = logger
        self._loaded: bool = False

    def load(self) -> bool:
        """Charge le fichier .env dans os.environ.

        Les variables deja presentes dans l'environnement ne sont
        pas ecrasees (override=False).

        Returns:
            True si le fichier a ete charge avec succes.
        """
        try:
            from dotenv import load_dotenv
        except ImportError:
            return False
        if not self._dotenv_path.exists():
            if self._logger:
                self._logger.log_warning(
                    f"Fichier .env introuvable : "
                    f"{self._dotenv_path}"
                )
            return False
        load_dotenv(
            dotenv_path=self._dotenv_path,
            override=False,
        )
        self._loaded = True
        return True

    def get(
        self,
        service: str,
        key: str,
    ) -> Optional[str]:
        """Charge le .env si necessaire puis lit la variable.

        Args:
            service: Nom du service (non utilise, pour
                compatibilite avec l'interface).
            key: Nom de la variable d'environnement.

        Returns:
            Valeur de la variable ou None.
        """
        if not self._loaded:
            self.load()
        value = os.environ.get(key.upper())
        return value if value else None

    def is_available(self) -> bool:
        """Indique si ce provider est operationnel.

        Returns:
            True si python-dotenv est installe et le fichier existe.
        """
        try:
            import dotenv  # noqa: F401
        except ImportError:
            return False
        return self._dotenv_path.exists()

    @property
    def source_name(self) -> str:
        """Nom court de la source.

        Returns:
            "dotenv"
        """
        return "dotenv"
