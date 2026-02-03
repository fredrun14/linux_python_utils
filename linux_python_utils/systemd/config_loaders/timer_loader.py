"""Chargeur de configuration pour les unités .timer systemd.

Ce module fournit une classe pour charger un fichier TOML et créer
un TimerConfig pour les unités systemd .timer.

Example:
    Chargement d'un TimerConfig depuis un fichier TOML:

        loader = TimerConfigLoader("config/app.toml")
        timer_config = loader.load()

    Fichier TOML attendu:

        [timer]
        description = "Mon timer quotidien"
        unit = "my-service.service"
        on_calendar = "daily"
        persistent = true
"""

from pathlib import Path
from typing import Any

from linux_python_utils.config import ConfigLoader
from linux_python_utils.systemd import TimerConfig
from linux_python_utils.systemd.config_loaders.base import TomlConfigLoader


class TimerConfigLoader(TomlConfigLoader[TimerConfig]):
    """Chargeur de configuration TOML pour TimerConfig.

    Cette classe lit un fichier TOML et crée un TimerConfig
    à partir de la section [timer].

    Attributes:
        DEFAULT_SECTION: Nom de la section par défaut ("timer").

    Example:
        >>> loader = TimerConfigLoader("config/flatpak.toml")
        >>> config = loader.load()
        >>> print(config.on_calendar)
        *-*-* 03:00:00
    """

    DEFAULT_SECTION: str = "timer"

    def __init__(
        self,
        toml_path: str | Path,
        config_loader: ConfigLoader | None = None
    ) -> None:
        """Initialise le loader pour TimerConfig.

        Args:
            toml_path: Chemin vers le fichier de configuration TOML.
            config_loader: Chargeur de configuration injectable (DIP).

        Raises:
            FileNotFoundError: Si le fichier TOML n'existe pas.
            tomllib.TOMLDecodeError: Si le TOML est invalide.
        """
        super().__init__(toml_path, config_loader)

    def load(self, section: str | None = None) -> TimerConfig:
        """Charge et retourne un TimerConfig.

        Args:
            section: Nom de la section à charger.
                Par défaut "timer".

        Returns:
            Instance de TimerConfig avec les valeurs du TOML.

        Raises:
            KeyError: Si la section n'existe pas.
            TypeError: Si les champs requis sont manquants.

        Example:
            >>> loader = TimerConfigLoader("config/app.toml")
            >>> config = loader.load()
            >>> config.persistent
            True
        """
        section_name = section or self.DEFAULT_SECTION
        data: dict[str, Any] = self._get_section(section_name)

        return TimerConfig(
            description=data["description"],
            unit=data["unit"],
            on_calendar=data.get("on_calendar", ""),
            on_boot_sec=data.get("on_boot_sec", ""),
            on_unit_active_sec=data.get("on_unit_active_sec", ""),
            persistent=data.get("persistent", False),
            randomized_delay_sec=data.get("randomized_delay_sec", ""),
        )

    def load_for_service(
        self,
        service_name: str,
        section: str | None = None
    ) -> TimerConfig:
        """Charge un TimerConfig pour un service spécifique.

        Remplace le champ 'unit' par le nom du service fourni,
        utile quand le nom du service est déterminé dynamiquement.

        Args:
            service_name: Nom du service cible (sans extension .service).
            section: Nom de la section à charger.

        Returns:
            Instance de TimerConfig avec unit défini sur le service.

        Example:
            >>> loader = TimerConfigLoader("config/app.toml")
            >>> config = loader.load_for_service("flatpak-update")
            >>> config.unit
            'flatpak-update.service'
        """
        section_name = section or self.DEFAULT_SECTION
        data: dict[str, Any] = self._get_section(section_name)

        # Ajouter l'extension .service si absente
        unit = service_name
        if not unit.endswith(".service"):
            unit = f"{unit}.service"

        return TimerConfig(
            description=data["description"],
            unit=unit,
            on_calendar=data.get("on_calendar", ""),
            on_boot_sec=data.get("on_boot_sec", ""),
            on_unit_active_sec=data.get("on_unit_active_sec", ""),
            persistent=data.get("persistent", False),
            randomized_delay_sec=data.get("randomized_delay_sec", ""),
        )
