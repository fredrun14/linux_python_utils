"""Tests pour le module systemd mount/automount.

Ce module contient les tests unitaires pour valider le comportement
des classes MountConfig, AutomountConfig et LinuxMountUnitManager.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from linux_python_utils.systemd import (
    MountConfig,
    AutomountConfig,
    LinuxMountUnitManager
)
from linux_python_utils.logging import Logger


class MockLogger(Logger):
    """Logger mock pour les tests.

    Attributes:
        messages: Liste des messages loggés sous forme de tuples (niveau, message).
    """

    def __init__(self) -> None:
        """Initialise le logger mock."""
        self.messages: list[tuple[str, str]] = []

    def log_info(self, message: str) -> None:
        """Enregistre un message info."""
        self.messages.append(("INFO", message))

    def log_warning(self, message: str) -> None:
        """Enregistre un message warning."""
        self.messages.append(("WARNING", message))

    def log_error(self, message: str) -> None:
        """Enregistre un message error."""
        self.messages.append(("ERROR", message))


class MockSystemdManager:
    """Mock du gestionnaire systemd pour les tests.

    Attributes:
        reload_called: Indique si reload_systemd a été appelé.
        enabled_units: Liste des unités activées.
        disabled_units: Liste des unités désactivées.
    """

    def __init__(self) -> None:
        """Initialise le mock systemd."""
        self.reload_called: bool = False
        self.enabled_units: list[str] = []
        self.disabled_units: list[str] = []

    def reload_systemd(self) -> bool:
        """Simule le rechargement de systemd."""
        self.reload_called = True
        return True

    def enable_unit(self, unit_name: str) -> bool:
        """Simule l'activation d'une unité."""
        self.enabled_units.append(unit_name)
        return True

    def disable_unit(
        self, unit_name: str, ignore_errors: bool = False
    ) -> bool:
        """Simule la désactivation d'une unité."""
        self.disabled_units.append(unit_name)
        return True

    def get_status(self, unit_name: str) -> str:
        """Retourne un statut simulé."""
        return "inactive"


@pytest.fixture
def mock_logger() -> MockLogger:
    """Fixture fournissant un logger mock."""
    return MockLogger()


@pytest.fixture
def mock_systemd() -> MockSystemdManager:
    """Fixture fournissant un gestionnaire systemd mock."""
    return MockSystemdManager()


@pytest.fixture
def mount_manager(
    mock_logger: MockLogger, mock_systemd: MockSystemdManager
) -> LinuxMountUnitManager:
    """Fixture fournissant un gestionnaire de montage configuré."""
    return LinuxMountUnitManager(mock_logger, mock_systemd)


@pytest.fixture
def temp_dir():
    """Fixture fournissant un répertoire temporaire."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


class TestPathToUnitName:
    """Tests pour la conversion chemin -> nom d'unité."""

    @pytest.mark.parametrize("mount_path,expected", [
        ("/media/nas", "media-nas"),
        ("/media/nas/backup/daily", "media-nas-backup-daily"),
        ("/media/nas/", "media-nas"),
        ("/mnt", "mnt"),
        ("media/nas", "media-nas"),
    ])
    def test_path_conversion(
        self, mount_manager: LinuxMountUnitManager, mount_path: str, expected: str
    ):
        """Vérifie la conversion de différents chemins en noms d'unité."""
        result = mount_manager.path_to_unit_name(mount_path)
        assert result == expected


class TestGenerateMountUnit:
    """Tests pour la génération de fichiers .mount via MountConfig.to_unit_file."""

    def test_basic_nfs_mount_contains_required_sections(self):
        """Vérifie que le fichier .mount contient toutes les sections requises."""
        # Arrange
        config = MountConfig(
            description="Sauvegarde NAS",
            what="192.168.1.10:/share",
            where="/media/nas/backup",
            type="nfs"
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "[Unit]" in result
        assert "Description=Sauvegarde NAS" in result
        assert "[Mount]" in result
        assert "What=192.168.1.10:/share" in result
        assert "Where=/media/nas/backup" in result
        assert "Type=nfs" in result
        assert "[Install]" in result
        assert "WantedBy=multi-user.target" in result

    def test_mount_with_options_includes_options_line(self):
        """Vérifie que les options de montage sont incluses."""
        # Arrange
        config = MountConfig(
            description="NFS avec options",
            what="192.168.1.10:/share",
            where="/media/nas",
            type="nfs",
            options="defaults,_netdev,noatime"
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "Options=defaults,_netdev,noatime" in result

    def test_cifs_mount_generates_correct_format(self):
        """Vérifie la génération correcte d'un montage CIFS."""
        # Arrange
        config = MountConfig(
            description="Partage Windows",
            what="//192.168.1.50/Documents",
            where="/mnt/windows",
            type="cifs",
            options="credentials=/etc/samba/credentials,uid=1000"
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "Type=cifs" in result
        assert "What=//192.168.1.50/Documents" in result
        assert "Options=credentials=/etc/samba/credentials,uid=1000" in result

    def test_mount_without_options_omits_options_line(self):
        """Vérifie l'absence de ligne Options= quand aucune option n'est définie."""
        # Arrange
        config = MountConfig(
            description="Test",
            what="server:/share",
            where="/mnt/test",
            type="nfs"
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "Options=" not in result


class TestGenerateAutomountUnit:
    """Tests pour la génération de fichiers .automount via to_unit_file."""

    def test_basic_automount_contains_required_sections(self):
        """Vérifie que le fichier .automount contient toutes les sections."""
        # Arrange
        config = AutomountConfig(
            description="Sauvegarde NAS",
            where="/media/nas/backup"
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "[Unit]" in result
        assert "Description=Automontage Sauvegarde NAS" in result
        assert "[Automount]" in result
        assert "Where=/media/nas/backup" in result
        assert "[Install]" in result
        assert "WantedBy=multi-user.target" in result

    def test_automount_with_timeout_includes_timeout_line(self):
        """Vérifie que le timeout est inclus quand spécifié."""
        # Arrange
        config = AutomountConfig(
            description="Test",
            where="/media/test",
            timeout_idle_sec=300
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "TimeoutIdleSec=300" in result

    def test_automount_without_timeout_omits_timeout_line(self):
        """Vérifie l'absence de TimeoutIdleSec= quand timeout est 0."""
        # Arrange
        config = AutomountConfig(
            description="Test",
            where="/media/test",
            timeout_idle_sec=0
        )

        # Act
        result = config.to_unit_file()

        # Assert
        assert "TimeoutIdleSec=" not in result


class TestInstallMountUnit:
    """Tests pour l'installation des unités mount."""

    def test_install_mount_only_creates_mount_file(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager,
        temp_dir: str
    ):
        """Vérifie que l'installation crée le fichier .mount."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = temp_dir
        config = MountConfig(
            description="Test",
            what="server:/share",
            where=os.path.join(temp_dir, "testmount"),
            type="nfs"
        )

        # Act
        result = manager.install_mount_unit(config, with_automount=False)

        # Assert
        assert result is True
        mount_file = os.path.join(
            temp_dir,
            f"{manager.path_to_unit_name(config.where)}.mount"
        )
        assert os.path.exists(mount_file)
        assert mock_systemd.reload_called

    def test_install_with_automount_creates_both_files(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager,
        temp_dir: str
    ):
        """Vérifie que l'installation avec automount crée les deux fichiers."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = temp_dir
        config = MountConfig(
            description="Test",
            what="server:/share",
            where=os.path.join(temp_dir, "testmount"),
            type="nfs"
        )

        # Act
        result = manager.install_mount_unit(
            config,
            with_automount=True,
            automount_timeout=300
        )

        # Assert
        assert result is True
        unit_name = manager.path_to_unit_name(config.where)
        mount_file = os.path.join(temp_dir, f"{unit_name}.mount")
        automount_file = os.path.join(temp_dir, f"{unit_name}.automount")
        assert os.path.exists(mount_file)
        assert os.path.exists(automount_file)

        with open(automount_file, encoding="utf-8") as f:
            content = f.read()
        assert "TimeoutIdleSec=300" in content

    def test_install_creates_mount_point_directory(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager,
        temp_dir: str
    ):
        """Vérifie que le point de montage est créé automatiquement."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = temp_dir
        mount_point = os.path.join(temp_dir, "new", "mount", "point")
        config = MountConfig(
            description="Test",
            what="server:/share",
            where=mount_point,
            type="nfs"
        )

        # Act
        result = manager.install_mount_unit(config)

        # Assert
        assert result is True
        assert os.path.isdir(mount_point)

    def test_install_with_permission_error_logs_error(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que les erreurs de permission sont loggées."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = "/etc/systemd/system"
        config = MountConfig(
            description="Test",
            what="server:/share",
            where="/root/restricted_mount",
            type="nfs"
        )

        # Act
        result = manager.install_mount_unit(config)

        # Assert - Le résultat dépend des permissions
        error_messages = [
            m for level, m in mock_logger.messages if level == "ERROR"
        ]
        if result is False:
            assert len(error_messages) > 0


class TestEnableDisableMount:
    """Tests pour l'activation et désactivation des montages."""

    def test_enable_mount_activates_mount_unit(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que enable_mount active l'unité .mount."""
        # Act
        result = mount_manager.enable_mount("/media/nas/backup")

        # Assert
        assert result is True
        assert "media-nas-backup.mount" in mock_systemd.enabled_units

    def test_enable_mount_with_automount_activates_automount_unit(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que enable_mount avec with_automount active l'unité .automount."""
        # Act
        result = mount_manager.enable_mount(
            "/media/nas/backup",
            with_automount=True
        )

        # Assert
        assert result is True
        assert "media-nas-backup.automount" in mock_systemd.enabled_units

    def test_disable_mount_deactivates_both_units(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que disable_mount désactive les unités .mount et .automount."""
        # Act
        result = mount_manager.disable_mount("/media/nas/backup")

        # Assert
        assert result is True
        assert "media-nas-backup.automount" in mock_systemd.disabled_units
        assert "media-nas-backup.mount" in mock_systemd.disabled_units


class TestRemoveMountUnit:
    """Tests pour la suppression des unités mount."""

    def test_remove_mount_unit_deletes_both_files(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager,
        temp_dir: str
    ):
        """Vérifie que remove_mount_unit supprime les deux fichiers."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = temp_dir
        mount_file = os.path.join(temp_dir, "media-nas.mount")
        automount_file = os.path.join(temp_dir, "media-nas.automount")
        Path(mount_file).write_text("[Unit]\n", encoding="utf-8")
        Path(automount_file).write_text("[Unit]\n", encoding="utf-8")

        # Act
        result = manager.remove_mount_unit("/media/nas")

        # Assert
        assert result is True
        assert not os.path.exists(mount_file)
        assert not os.path.exists(automount_file)
        assert mock_systemd.reload_called

    def test_remove_nonexistent_unit_succeeds_silently(
        self,
        mock_logger: MockLogger,
        mock_systemd: MockSystemdManager,
        temp_dir: str
    ):
        """Vérifie que la suppression d'unités inexistantes ne génère pas d'erreur."""
        # Arrange
        manager = LinuxMountUnitManager(mock_logger, mock_systemd)
        manager.SYSTEMD_UNIT_PATH = temp_dir

        # Act
        result = manager.remove_mount_unit("/media/nonexistent")

        # Assert
        assert result is True


class TestMountStatus:
    """Tests pour la vérification du statut de montage."""

    def test_get_mount_status_returns_unit_status(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que get_mount_status retourne le statut de l'unité."""
        # Arrange
        mock_systemd.get_status = Mock(return_value="active")

        # Act
        result = mount_manager.get_mount_status("/media/nas")

        # Assert
        assert result == "active"
        mock_systemd.get_status.assert_called_with("media-nas.mount")

    def test_is_mounted_returns_true_when_active(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que is_mounted retourne True quand l'unité est active."""
        # Arrange
        mock_systemd.get_status = Mock(return_value="active")

        # Act & Assert
        assert mount_manager.is_mounted("/media/nas") is True

    def test_is_mounted_returns_false_when_inactive(
        self,
        mount_manager: LinuxMountUnitManager,
        mock_systemd: MockSystemdManager
    ):
        """Vérifie que is_mounted retourne False quand l'unité est inactive."""
        # Arrange
        mock_systemd.get_status = Mock(return_value="inactive")

        # Act & Assert
        assert mount_manager.is_mounted("/media/nas") is False


class TestMountConfigDataclass:
    """Tests pour la dataclass MountConfig."""

    def test_mount_config_creation_with_required_fields(self):
        """Vérifie la création avec les champs requis."""
        # Arrange & Act
        config = MountConfig(
            description="Test mount",
            what="server:/share",
            where="/mnt/test",
            type="nfs"
        )

        # Assert
        assert config.description == "Test mount"
        assert config.what == "server:/share"
        assert config.where == "/mnt/test"
        assert config.type == "nfs"
        assert config.options == ""

    def test_mount_config_with_options(self):
        """Vérifie la création avec des options."""
        # Arrange & Act
        config = MountConfig(
            description="Test",
            what="server:/share",
            where="/mnt/test",
            type="nfs",
            options="ro,noexec"
        )

        # Assert
        assert config.options == "ro,noexec"


class TestAutomountConfigDataclass:
    """Tests pour la dataclass AutomountConfig."""

    def test_automount_config_creation_with_required_fields(self):
        """Vérifie la création avec les champs requis."""
        # Arrange & Act
        config = AutomountConfig(
            description="Test automount",
            where="/mnt/test"
        )

        # Assert
        assert config.description == "Test automount"
        assert config.where == "/mnt/test"
        assert config.timeout_idle_sec == 0

    def test_automount_config_with_timeout(self):
        """Vérifie la création avec un timeout personnalisé."""
        # Arrange & Act
        config = AutomountConfig(
            description="Test",
            where="/mnt/test",
            timeout_idle_sec=600
        )

        # Assert
        assert config.timeout_idle_sec == 600
