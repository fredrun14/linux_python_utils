"""Tests pour le module notification."""

import pytest

from linux_python_utils.notification import NotificationConfig


class TestNotificationConfig:
    """Tests pour la dataclass NotificationConfig."""

    def test_creation_with_required_fields(self):
        """Vérifie la création avec les champs requis."""
        config = NotificationConfig(
            title="Test",
            message_success="Succès",
            message_failure="Échec"
        )
        assert config.title == "Test"
        assert config.message_success == "Succès"
        assert config.message_failure == "Échec"

    def test_default_icons(self):
        """Vérifie les icônes par défaut."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        assert config.icon_success == "software-update-available"
        assert config.icon_failure == "dialog-error"

    def test_custom_icons(self):
        """Vérifie les icônes personnalisées."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO",
            icon_success="emblem-ok",
            icon_failure="emblem-error"
        )
        assert config.icon_success == "emblem-ok"
        assert config.icon_failure == "emblem-error"

    def test_raises_on_empty_title(self):
        """Vérifie que __post_init__ lève une erreur si title est vide."""
        with pytest.raises(ValueError, match="title est requis"):
            NotificationConfig(
                title="",
                message_success="OK",
                message_failure="KO"
            )

    def test_raises_on_empty_message_success(self):
        """Vérifie l'erreur si message_success est vide."""
        with pytest.raises(ValueError, match="message_success est requis"):
            NotificationConfig(
                title="Test",
                message_success="",
                message_failure="KO"
            )

    def test_raises_on_empty_message_failure(self):
        """Vérifie l'erreur si message_failure est vide."""
        with pytest.raises(ValueError, match="message_failure est requis"):
            NotificationConfig(
                title="Test",
                message_success="OK",
                message_failure=""
            )

    def test_is_frozen(self):
        """Vérifie que la dataclass est immutable."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        with pytest.raises(AttributeError):
            config.title = "Nouveau titre"


class TestNotificationConfigToBashFunction:
    """Tests pour NotificationConfig.to_bash_function()."""

    def test_contains_function_definition(self):
        """Vérifie la présence de la définition de fonction."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        result = config.to_bash_function()
        assert "send_notification()" in result

    def test_contains_local_variables(self):
        """Vérifie la présence des variables locales."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        result = config.to_bash_function()
        assert 'local title="$1"' in result
        assert 'local message="$2"' in result
        assert 'local icon="$3"' in result

    def test_contains_loginctl_command(self):
        """Vérifie la présence de loginctl pour lister les utilisateurs."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        result = config.to_bash_function()
        assert "loginctl list-users" in result

    def test_contains_notify_send(self):
        """Vérifie la présence de notify-send."""
        config = NotificationConfig(
            title="Test",
            message_success="OK",
            message_failure="KO"
        )
        result = config.to_bash_function()
        assert "notify-send" in result


class TestNotificationConfigToBashCalls:
    """Tests pour les méthodes to_bash_call_*()."""

    def test_to_bash_call_success(self):
        """Vérifie la génération de l'appel pour le succès."""
        config = NotificationConfig(
            title="Flatpak",
            message_success="Mise à jour OK",
            message_failure="Échec",
            icon_success="emblem-ok"
        )
        result = config.to_bash_call_success()
        assert 'send_notification "Flatpak"' in result
        assert '"Mise à jour OK"' in result
        assert '"emblem-ok"' in result

    def test_to_bash_call_failure(self):
        """Vérifie la génération de l'appel pour l'échec."""
        config = NotificationConfig(
            title="Flatpak",
            message_success="OK",
            message_failure="Mise à jour échouée",
            icon_failure="dialog-error"
        )
        result = config.to_bash_call_failure()
        assert 'send_notification "Flatpak"' in result
        assert '"Mise à jour échouée"' in result
        assert '"dialog-error"' in result
