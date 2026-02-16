"""Tests pour le module systemd.executor."""

from unittest.mock import MagicMock

import pytest

from linux_python_utils.systemd.executor import (
    SystemdExecutor,
    UserSystemdExecutor,
)


class TestSystemdExecutorValidation:
    """Tests pour la validation des noms d'unités dans SystemdExecutor."""

    def _make_executor(self) -> SystemdExecutor:
        """Crée un executor avec un logger mock."""
        logger = MagicMock()
        return SystemdExecutor(logger)

    def test_enable_unit_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans enable_unit."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.enable_unit("bad;name.service")

    def test_disable_unit_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans disable_unit."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.disable_unit("../etc.service")

    def test_start_unit_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans start_unit."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.start_unit("$(cmd).service")

    def test_stop_unit_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans stop_unit."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.stop_unit("bad name.service")

    def test_restart_unit_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans restart_unit."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.restart_unit(";evil.service")

    def test_get_status_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans get_status."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.get_status("../passwd.service")

    def test_is_enabled_rejette_nom_invalide(self):
        """Vérifie le rejet d'un nom invalide dans is_enabled."""
        executor = self._make_executor()
        with pytest.raises(ValueError, match="invalide"):
            executor.is_enabled("bad;cmd.timer")

    def test_nom_valide_accepte(self):
        """Vérifie que les noms valides passent la validation."""
        executor = self._make_executor()
        # Ne devrait pas lever d'exception (échouera au subprocess)
        # On vérifie juste que la validation passe
        try:
            executor.get_status("backup.service")
        except ValueError:
            pytest.fail("Nom valide rejeté par la validation")


class TestUserSystemdExecutorValidation:
    """Tests pour la validation dans UserSystemdExecutor."""

    def test_enable_unit_rejette_nom_invalide(self):
        """Vérifie le rejet dans l'executor utilisateur."""
        logger = MagicMock()
        executor = UserSystemdExecutor(logger)
        with pytest.raises(ValueError, match="invalide"):
            executor.enable_unit("bad;name.service")
