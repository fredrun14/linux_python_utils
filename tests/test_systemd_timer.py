"""Tests pour le module systemd.timer."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from linux_python_utils.systemd.base import TimerConfig
from linux_python_utils.systemd.timer import LinuxTimerUnitManager
from linux_python_utils.systemd.user_timer import LinuxUserTimerUnitManager


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


class TestLinuxTimerListTimers:
    """Tests pour LinuxTimerUnitManager.list_timers."""

    def _make_manager(self) -> LinuxTimerUnitManager:
        """Crée un manager avec des mocks."""
        logger = MagicMock()
        executor = MagicMock()
        return LinuxTimerUnitManager(logger, executor)

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_json_valide(self, mock_run):
        """Vérifie le parsing d'une réponse JSON valide."""
        data = [
            {"unit": "backup.timer", "activates": "backup.service",
             "next": "Mon 2026-01-01", "left": "1h",
             "last": "Sun 2025-12-31", "passed": "23h"}
        ]
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(data), stderr=""
        )
        manager = self._make_manager()
        result = manager.list_timers()
        assert len(result) == 1
        assert result[0]["unit"] == "backup.timer"
        assert result[0]["activates"] == "backup.service"

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_json_vide(self, mock_run):
        """Vérifie le parsing d'une liste JSON vide."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="[]", stderr=""
        )
        manager = self._make_manager()
        result = manager.list_timers()
        assert result == []

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_fallback_texte(self, mock_run):
        """Vérifie le fallback texte si JSON non supporté."""
        # Premier appel : JSON échoue
        fail_result = MagicMock(
            returncode=1,
            stdout="",
            stderr="unknown option '--output=json'"
        )
        # Deuxième appel : texte réussit
        text_output = (
            "NEXT LEFT LAST PASSED UNIT ACTIVATES\n"
            "Mon 2026-01-01 1h ago Sun backup.timer backup.service\n"
        )
        text_result = MagicMock(
            returncode=0, stdout=text_output, stderr=""
        )
        mock_run.side_effect = [fail_result, text_result]
        manager = self._make_manager()
        result = manager.list_timers()
        assert len(result) == 1
        assert result[0]["unit"] == "backup.timer"

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_erreur_subprocess(self, mock_run):
        """Vérifie que RuntimeError est levée sur erreur."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="",
            stderr="Failed to connect to bus"
        )
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Erreur systemctl"):
            manager.list_timers()

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_systemctl_introuvable(self, mock_run):
        """Vérifie RuntimeError si systemctl n'existe pas."""
        mock_run.side_effect = FileNotFoundError("systemctl")
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Impossible"):
            manager.list_timers()

    @patch("linux_python_utils.systemd.timer.subprocess.run")
    def test_list_timers_os_error(self, mock_run):
        """Vérifie RuntimeError sur OSError."""
        mock_run.side_effect = OSError("permission denied")
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Impossible"):
            manager.list_timers()


class TestLinuxUserTimerListTimers:
    """Tests pour LinuxUserTimerUnitManager.list_timers."""

    def _make_manager(self) -> LinuxUserTimerUnitManager:
        """Crée un manager utilisateur avec des mocks."""
        logger = MagicMock()
        executor = MagicMock()
        return LinuxUserTimerUnitManager(logger, executor)

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_json_valide(self, mock_run):
        """Vérifie le parsing d'une réponse JSON valide."""
        data = [
            {"unit": "backup.timer", "activates": "backup.service",
             "next": "", "left": "", "last": "", "passed": ""}
        ]
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(data), stderr=""
        )
        manager = self._make_manager()
        result = manager.list_timers()
        assert len(result) == 1
        assert result[0]["unit"] == "backup.timer"

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_json_vide(self, mock_run):
        """Vérifie le parsing d'une liste JSON vide."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="[]", stderr=""
        )
        manager = self._make_manager()
        result = manager.list_timers()
        assert result == []

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_fallback_texte(self, mock_run):
        """Vérifie le fallback texte si JSON non supporté."""
        fail_result = MagicMock(
            returncode=1,
            stdout="",
            stderr="unknown option '--output=json'"
        )
        text_output = (
            "NEXT LEFT LAST PASSED UNIT ACTIVATES\n"
            "Mon 2026-01-01 1h ago Sun user.timer user.service\n"
        )
        text_result = MagicMock(
            returncode=0, stdout=text_output, stderr=""
        )
        mock_run.side_effect = [fail_result, text_result]
        manager = self._make_manager()
        result = manager.list_timers()
        assert len(result) == 1
        assert result[0]["unit"] == "user.timer"

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_erreur_subprocess(self, mock_run):
        """Vérifie que RuntimeError est levée sur erreur."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="",
            stderr="Failed to connect to bus"
        )
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Erreur systemctl"):
            manager.list_timers()

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_systemctl_introuvable(self, mock_run):
        """Vérifie RuntimeError si systemctl n'existe pas."""
        mock_run.side_effect = FileNotFoundError("systemctl")
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Impossible"):
            manager.list_timers()

    @patch("linux_python_utils.systemd.user_timer.subprocess.run")
    def test_list_timers_os_error(self, mock_run):
        """Vérifie RuntimeError sur OSError."""
        mock_run.side_effect = OSError("permission denied")
        manager = self._make_manager()
        with pytest.raises(RuntimeError, match="Impossible"):
            manager.list_timers()
