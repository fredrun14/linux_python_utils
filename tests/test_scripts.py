"""Tests pour le module scripts."""

from unittest.mock import MagicMock, patch
import pytest

from linux_python_utils.notification import NotificationConfig
from linux_python_utils.scripts import BashScriptConfig, BashScriptInstaller


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
        assert "Flatpak Update" in result
        assert "Mise à jour réussie" in result
        assert "Échec de la mise à jour" in result
        assert "emblem-ok" in result
        assert "emblem-error" in result


class TestBashScriptInstaller:
    """Tests pour la classe BashScriptInstaller."""

    def setup_method(self):
        """Initialise les mocks pour chaque test."""
        self.mock_logger = MagicMock()
        self.mock_file_manager = MagicMock()
        self.installer = BashScriptInstaller(
            self.mock_logger,
            self.mock_file_manager
        )
        self.config = BashScriptConfig(exec_command="echo 'test'")

    def test_install_creates_file_when_not_exists(self):
        """Vérifie que le fichier est créé s'il n'existe pas."""
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = True

        with patch("os.chmod"):
            result = self.installer.install("/tmp/test.sh", self.config)

        assert result is True
        self.mock_file_manager.create_file.assert_called_once()

    def test_install_skips_existing_file(self):
        """Vérifie que l'installation est ignorée si le fichier existe."""
        self.mock_file_manager.file_exists.return_value = True

        result = self.installer.install("/tmp/test.sh", self.config)

        assert result is True
        self.mock_file_manager.create_file.assert_not_called()
        self.mock_logger.log_info.assert_called()

    def test_install_returns_false_on_create_failure(self):
        """Vérifie le retour False si la création échoue."""
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = False

        result = self.installer.install("/tmp/test.sh", self.config)

        assert result is False
        self.mock_logger.log_error.assert_called()

    def test_install_sets_executable_permission(self):
        """Vérifie que le script est rendu exécutable."""
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = True

        with patch("os.chmod") as mock_chmod:
            self.installer.install("/tmp/test.sh", self.config)
            mock_chmod.assert_called_once_with("/tmp/test.sh", 0o755)

    def test_install_returns_false_on_chmod_failure(self):
        """Vérifie le retour False si chmod échoue."""
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = True

        with patch("os.chmod", side_effect=OSError("Permission denied")):
            result = self.installer.install("/tmp/test.sh", self.config)

        assert result is False
        self.mock_logger.log_error.assert_called()

    def test_install_generates_correct_content(self):
        """Vérifie que le contenu généré est correct."""
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = True

        with patch("os.chmod"):
            self.installer.install("/tmp/test.sh", self.config)

        call_args = self.mock_file_manager.create_file.call_args
        content = call_args[0][1]
        assert "#!/bin/bash" in content
        assert "echo 'test'" in content

    def test_exists_delegates_to_file_manager(self):
        """Vérifie que exists() délègue au file_manager."""
        self.mock_file_manager.file_exists.return_value = True

        result = self.installer.exists("/tmp/test.sh")

        assert result is True
        self.mock_file_manager.file_exists.assert_called_once_with(
            "/tmp/test.sh"
        )

    def test_custom_default_mode(self):
        """Vérifie l'utilisation d'un mode personnalisé."""
        installer = BashScriptInstaller(
            self.mock_logger,
            self.mock_file_manager,
            default_mode=0o700
        )
        self.mock_file_manager.file_exists.return_value = False
        self.mock_file_manager.create_file.return_value = True

        with patch("os.chmod") as mock_chmod:
            installer.install("/tmp/test.sh", self.config)
            mock_chmod.assert_called_once_with("/tmp/test.sh", 0o700)
