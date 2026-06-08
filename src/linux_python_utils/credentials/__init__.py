"""Module de gestion des credentials pour applications Linux.

Fournit une chaine de priorite configurable :
    Shell env vars -> fichier .env (python-dotenv) -> keyring systeme

Compatibilite keyring : KWallet (KDE Plasma 6), KeePassXC (avec
"Enable Secret Service" active), GNOME Keyring.

Dependances optionnelles :
    pip install python-dotenv   # pour DotEnvCredentialProvider
    pip install keyring         # pour KeyringCredentialProvider

Exemple d'utilisation :

    from linux_python_utils.credentials import CredentialManager

    manager = CredentialManager.from_dotenv(
        service="monapp",
        dotenv_path=Path("config/.env"),
    )
    password = manager.get("API_PASSWORD")
    manager.store("API_PASSWORD", new_password)
"""

from linux_python_utils.credentials.base import (
    CredentialProvider,
    CredentialStore,
)
from linux_python_utils.credentials.chain import CredentialChain
from linux_python_utils.credentials.exceptions import (
    CredentialError,
    CredentialNotFoundError,
    CredentialProviderUnavailableError,
    CredentialStoreError,
)
from linux_python_utils.credentials.manager import CredentialManager
from linux_python_utils.credentials.models import (
    Credential,
    CredentialKey,
)
from linux_python_utils.credentials.providers import (
    DotEnvCredentialProvider,
    EnvCredentialProvider,
    KeyringCredentialProvider,
)

__all__ = [
    "Credential",
    "CredentialChain",
    "CredentialError",
    "CredentialKey",
    "CredentialManager",
    "CredentialNotFoundError",
    "CredentialProvider",
    "CredentialProviderUnavailableError",
    "CredentialStore",
    "CredentialStoreError",
    "DotEnvCredentialProvider",
    "EnvCredentialProvider",
    "KeyringCredentialProvider",
]
