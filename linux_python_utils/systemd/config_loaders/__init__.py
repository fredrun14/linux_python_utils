"""Chargeurs de configuration TOML pour les unités systemd.

Ce module fournit des classes pour charger des fichiers TOML et créer
les dataclasses de configuration systemd correspondantes.

Classes disponibles:
    TomlConfigLoader: Classe de base abstraite pour tous les loaders.
    ServiceConfigLoader: Charge un TOML vers ServiceConfig.
    TimerConfigLoader: Charge un TOML vers TimerConfig.
    MountConfigLoader: Charge un TOML vers MountConfig.
    BashScriptConfigLoader: Charge un TOML vers BashScriptConfig.

Example:
    Chargement d'une configuration de service:

        from linux_python_utils.systemd.config_loaders import (
            ServiceConfigLoader,
        )

        loader = ServiceConfigLoader("config/app.toml")
        service_config = loader.load()

    Chargement d'une configuration de timer:

        from linux_python_utils.systemd.config_loaders import TimerConfigLoader

        loader = TimerConfigLoader("config/app.toml")
        timer_config = loader.load_for_service("my-service")

Architecture:
    Tous les loaders héritent de TomlConfigLoader[T] qui fournit:
    - Chargement du fichier TOML via ConfigLoader injectable (DIP)
    - Méthodes utilitaires pour extraire des sections
    - Propriété config pour accéder au dictionnaire brut

"""

from linux_python_utils.systemd.config_loaders.base import TomlConfigLoader
from linux_python_utils.systemd.config_loaders.service_loader import (
    ServiceConfigLoader,
)
from linux_python_utils.systemd.config_loaders.timer_loader import (
    TimerConfigLoader,
)
from linux_python_utils.systemd.config_loaders.mount_loader import (
    MountConfigLoader,
)
from linux_python_utils.systemd.config_loaders.script_loader import (
    BashScriptConfigLoader,
)

__all__ = [
    # Classe de base
    "TomlConfigLoader",
    # Loaders spécialisés
    "ServiceConfigLoader",
    "TimerConfigLoader",
    "MountConfigLoader",
    "BashScriptConfigLoader",
]
