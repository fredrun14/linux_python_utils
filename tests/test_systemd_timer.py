"""Tests pour le module systemd.timer."""

import pytest

from linux_python_utils.systemd.base import TimerConfig


class TestTimerConfig:
    """Tests pour la dataclass TimerConfig."""

    def test_timer_name_extracts_from_service(self):
        """Vérifie l'extraction du nom du timer depuis l'unité cible."""
        config = TimerConfig(
            description="Test",
            unit="backup.service"
        )
        assert config.timer_name == "backup"

    def test_timer_name_handles_complex_unit_names(self):
        """Vérifie l'extraction avec des noms d'unités complexes."""
        config = TimerConfig(
            description="Test",
            unit="my-backup-task.service"
        )
        assert config.timer_name == "my-backup-task"

    def test_post_init_raises_on_empty_unit(self):
        """Vérifie que __post_init__ lève une erreur si unit est vide."""
        with pytest.raises(ValueError, match="'unit' est requis"):
            TimerConfig(description="Test", unit="")


class TestTimerConfigToUnitFile:
    """Tests pour TimerConfig.to_unit_file()."""

    def test_basic_timer_contains_required_sections(self):
        """Vérifie que le fichier .timer contient toutes les sections."""
        config = TimerConfig(
            description="Sauvegarde quotidienne",
            unit="backup.service",
            on_calendar="daily"
        )

        result = config.to_unit_file()

        assert "[Unit]" in result
        assert "Description=Sauvegarde quotidienne" in result
        assert "[Timer]" in result
        assert "Unit=backup.service" in result
        assert "OnCalendar=daily" in result
        assert "[Install]" in result
        assert "WantedBy=timers.target" in result

    def test_timer_with_on_boot_sec(self):
        """Vérifie l'inclusion de OnBootSec."""
        config = TimerConfig(
            description="Démarrage différé",
            unit="startup-task.service",
            on_boot_sec="5min"
        )

        result = config.to_unit_file()

        assert "OnBootSec=5min" in result

    def test_timer_with_on_unit_active_sec(self):
        """Vérifie l'inclusion de OnUnitActiveSec."""
        config = TimerConfig(
            description="Tâche récurrente",
            unit="recurring.service",
            on_unit_active_sec="1h"
        )

        result = config.to_unit_file()

        assert "OnUnitActiveSec=1h" in result

    def test_timer_with_persistent_true(self):
        """Vérifie l'inclusion de Persistent=true."""
        config = TimerConfig(
            description="Timer persistant",
            unit="persistent.service",
            on_calendar="weekly",
            persistent=True
        )

        result = config.to_unit_file()

        assert "Persistent=true" in result

    def test_timer_with_persistent_false_omits_line(self):
        """Vérifie l'absence de Persistent quand False."""
        config = TimerConfig(
            description="Timer non persistant",
            unit="non-persistent.service",
            on_calendar="daily",
            persistent=False
        )

        result = config.to_unit_file()

        assert "Persistent" not in result

    def test_timer_with_randomized_delay(self):
        """Vérifie l'inclusion de RandomizedDelaySec."""
        config = TimerConfig(
            description="Timer avec délai aléatoire",
            unit="random.service",
            on_calendar="hourly",
            randomized_delay_sec="15min"
        )

        result = config.to_unit_file()

        assert "RandomizedDelaySec=15min" in result

    def test_timer_without_optional_fields_omits_them(self):
        """Vérifie l'absence des champs optionnels non définis."""
        config = TimerConfig(
            description="Timer minimal",
            unit="minimal.service"
        )

        result = config.to_unit_file()

        assert "OnCalendar=" not in result
        assert "OnBootSec=" not in result
        assert "OnUnitActiveSec=" not in result
        assert "Persistent" not in result
        assert "RandomizedDelaySec=" not in result

    def test_timer_with_all_options(self):
        """Vérifie un timer avec toutes les options."""
        config = TimerConfig(
            description="Timer complet",
            unit="complete.service",
            on_calendar="*-*-* 06:00:00",
            on_boot_sec="10min",
            on_unit_active_sec="30min",
            persistent=True,
            randomized_delay_sec="5min"
        )

        result = config.to_unit_file()

        assert "OnCalendar=*-*-* 06:00:00" in result
        assert "OnBootSec=10min" in result
        assert "OnUnitActiveSec=30min" in result
        assert "Persistent=true" in result
        assert "RandomizedDelaySec=5min" in result
