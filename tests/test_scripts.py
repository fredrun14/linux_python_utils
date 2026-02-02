"""Tests pour le module scripts."""

import pytest

from linux_python_utils.notification import NotificationConfig
from linux_python_utils.scripts import BashScriptConfig


class TestBashScriptConfig:
    """Tests pour la dataclass BashScriptConfig."""

    def test_creation_with_command_only(self):
        """Vérifie la création avec uniquement la commande."""
        config = BashScriptConfig(exec_command="echo 'Hello'")
        assert config.exec_command == "echo 'Hello'"
        assert config.notification is None

    def test_creation_with_notification(self):
        """Vérifie la création avec notification."""
        notif = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        config = BashScriptConfig(
            exec_command="ls -la",
            notification=notif
        )
        assert config.exec_command == "ls -la"
        assert config.notification is notif

    def test_raises_on_empty_exec_command(self):
        """Vérifie l'erreur si exec_command est vide."""
        with pytest.raises(ValueError, match="exec_command est requis"):
            BashScriptConfig(exec_command="")

    def test_is_frozen(self):
        """Vérifie que la dataclass est immutable."""
        config = BashScriptConfig(exec_command="echo test")
        with pytest.raises(AttributeError):
            config.exec_command = "autre commande"


class TestBashScriptConfigToBashScript:
    """Tests pour BashScriptConfig.to_bash_script()."""

    def test_simple_script_starts_with_shebang(self):
        """Vérifie que le script simple commence par le shebang."""
        config = BashScriptConfig(exec_command="echo 'Hello'")
        result = config.to_bash_script()
        assert result.startswith("#!/bin/bash")

    def test_simple_script_contains_command(self):
        """Vérifie que le script simple contient la commande."""
        config = BashScriptConfig(exec_command="/usr/bin/flatpak update -y")
        result = config.to_bash_script()
        assert "/usr/bin/flatpak update -y" in result

    def test_simple_script_is_minimal(self):
        """Vérifie que le script simple est minimal (pas de notification)."""
        config = BashScriptConfig(exec_command="echo test")
        result = config.to_bash_script()
        assert "send_notification" not in result
        assert "exit_code" not in result

    def test_script_with_notification_contains_function(self):
        """Vérifie la présence de send_notification avec notification."""
        notif = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        config = BashScriptConfig(
            exec_command="echo test",
            notification=notif
        )
        result = config.to_bash_script()
        assert "send_notification()" in result

    def test_script_with_notification_captures_exit_code(self):
        """Vérifie la capture du code de retour."""
        notif = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        config = BashScriptConfig(
            exec_command="echo test",
            notification=notif
        )
        result = config.to_bash_script()
        assert "exit_code=$?" in result
        assert "exit $exit_code" in result

    def test_script_with_notification_has_conditional(self):
        """Vérifie la présence de la condition if/else."""
        notif = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        config = BashScriptConfig(
            exec_command="echo test",
            notification=notif
        )
        result = config.to_bash_script()
        assert "if [ $exit_code -eq 0 ]" in result
        assert "else" in result
        assert "fi" in result

    def test_script_with_notification_uses_config_values(self):
        """Vérifie l'utilisation des valeurs de configuration."""
        notif = NotificationConfig(
            title="Flatpak Update",
            message_success="Mise à jour réussie",
            message_failure="Échec de la mise à jour",
            icon_success="emblem-ok",
            icon_failure="emblem-error"
        )
        config = BashScriptConfig(
            exec_command="/usr/bin/flatpak update -y",
            notification=notif
        )
        result = config.to_bash_script()
        assert '"Flatpak Update"' in result
        assert '"Mise à jour réussie"' in result
        assert '"Échec de la mise à jour"' in result
        assert '"emblem-ok"' in result
        assert '"emblem-error"' in result
