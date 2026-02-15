"""Chargeurs de configuration pour les unités systemd.

Ce module fournit des classes pour charger des fichiers de configuration
(TOML ou JSON) et créer les dataclasses systemd correspondantes.

Classes disponibles:
    ConfigFileLoader: Classe de base abstraite pour tous les loaders.
    ServiceConfigLoader: Charge un fichier vers ServiceConfig.
    TimerConfigLoader: Charge un fichier vers TimerConfig.
    MountConfigLoader: Charge un fichier vers MountConfig.
    BashScriptConfigLoader: Charge un fichier vers BashScriptConfig.
    TomlConfigLoader: Alias deprecated pour ConfigFileLoader.

Example:
    Chargement d'une configuration de service depuis TOML:

        from linux_python_utils.systemd.config_loaders import (
            ServiceConfigLoader,
        )

        loader = ServiceConfigLoader("config/app.toml")
        service_config = loader.load()

    Chargement depuis JSON:

        loader = ServiceConfigLoader("config/app.json")
        service_config = loader.load()

    Chargement d'une configuration de timer:

        from linux_python_utils.systemd.config_loaders import TimerConfigLoader

        loader = TimerConfigLoader("config/app.toml")
        timer_config = loader.load_for_service("my-service")

Architecture:
    Tous les loaders héritent de ConfigFileLoader[T] qui fournit:
    - Chargement du fichier via ConfigLoader injectable (DIP)
    - Support automatique TOML et JSON (détection par extension)
    - Méthodes utilitaires pour extraire des sections
    - Propriété config pour accéder au dictionnaire brut

"""

# # from linux_python_utils.systemd.config_loaders.base import (
# #     ConfigFileLoader,
# #     TomlConfigLoader,
# )
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
    # Loaders spécialisés
    "ServiceConfigLoader",
    "TimerConfigLoader",
    "MountConfigLoader",
    "BashScriptConfigLoader",
    # Alias deprecated pour rétrocompatibilité
    # "TomlConfigLoader",
]
