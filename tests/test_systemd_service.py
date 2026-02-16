"""Tests pour le module systemd.service."""

import os
import shutil
import tempfile
from unittest.mock import MagicMock

import pytest

from linux_python_utils.systemd.base import ServiceConfig
from linux_python_utils.systemd.service import LinuxServiceUnitManager
from linux_python_utils.systemd.user_service import LinuxUserServiceUnitManager


class TestServiceConfig:
    """Tests pour la dataclass ServiceConfig."""

    def test_post_init_raises_on_empty_exec_start(self):
        """Vérifie que __post_init__ lève une erreur si exec_start est vide."""
        with pytest.raises(ValueError, match="'exec_start' est requis"):
            ServiceConfig(description="Test", exec_start="")

    def test_default_values(self):
        """Vérifie les valeurs par défaut."""
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/test"
        )

        assert config.type == "simple"
        assert config.user == ""
        assert config.group == ""
        assert config.working_directory == ""
        assert config.environment == {}
        assert config.restart == "no"
        assert config.restart_sec == 0
        assert config.wanted_by == "multi-user.target"


class TestServiceConfigToUnitFile:
    """Tests pour ServiceConfig.to_unit_file()."""

    def test_basic_service_contains_required_sections(self):
        """Vérifie que le fichier .service contient toutes les sections."""
        config = ServiceConfig(
            description="Mon service",
            exec_start="/usr/bin/my-daemon"
        )

        result = config.to_unit_file()

        assert "[Unit]" in result
        assert "Description=Mon service" in result
        assert "[Service]" in result
        assert "Type=simple" in result
        assert "ExecStart=/usr/bin/my-daemon" in result
        assert "[Install]" in result
        assert "WantedBy=multi-user.target" in result

    def test_service_with_user_and_group(self):
        """Vérifie l'inclusion de User et Group."""
        config = ServiceConfig(
            description="Service avec utilisateur",
            exec_start="/usr/bin/daemon",
            user="www-data",
            group="www-data"
        )

        result = config.to_unit_file()

        assert "User=www-data" in result
        assert "Group=www-data" in result

    def test_service_with_working_directory(self):
        """Vérifie l'inclusion de WorkingDirectory."""
        config = ServiceConfig(
            description="Service avec répertoire",
            exec_start="/usr/bin/daemon",
            working_directory="/var/lib/myapp"
        )

        result = config.to_unit_file()

        assert "WorkingDirectory=/var/lib/myapp" in result

    def test_service_with_environment_variables(self):
        """Vérifie l'inclusion des variables d'environnement."""
        config = ServiceConfig(
            description="Service avec env",
            exec_start="/usr/bin/daemon",
            environment={"HOME": "/var/lib/myapp", "PATH": "/usr/bin"}
        )

        result = config.to_unit_file()

        assert "Environment=HOME=/var/lib/myapp" in result
        assert "Environment=PATH=/usr/bin" in result

    def test_service_with_restart_policy(self):
        """Vérifie l'inclusion de Restart."""
        config = ServiceConfig(
            description="Service avec redémarrage",
            exec_start="/usr/bin/daemon",
            restart="on-failure"
        )

        result = config.to_unit_file()

        assert "Restart=on-failure" in result

    def test_service_with_restart_sec(self):
        """Vérifie l'inclusion de RestartSec."""
        config = ServiceConfig(
            description="Service avec délai",
            exec_start="/usr/bin/daemon",
            restart="always",
            restart_sec=10
        )

        result = config.to_unit_file()

        assert "Restart=always" in result
        assert "RestartSec=10" in result

    def test_service_restart_no_omits_restart_lines(self):
        """Vérifie l'absence de Restart quand restart='no'."""
        config = ServiceConfig(
            description="Service sans redémarrage",
            exec_start="/usr/bin/daemon",
            restart="no",
            restart_sec=10
        )

        result = config.to_unit_file()

        assert "Restart=" not in result
        assert "RestartSec=" not in result

    def test_service_with_custom_wanted_by(self):
        """Vérifie l'utilisation d'un WantedBy personnalisé."""
        config = ServiceConfig(
            description="Service graphique",
            exec_start="/usr/bin/gui-app",
            wanted_by="graphical.target"
        )

        result = config.to_unit_file()

        assert "WantedBy=graphical.target" in result

    def test_service_type_oneshot(self):
        """Vérifie un service de type oneshot."""
        config = ServiceConfig(
            description="Script ponctuel",
            exec_start="/usr/local/bin/backup.sh",
            type="oneshot"
        )

        result = config.to_unit_file()

        assert "Type=oneshot" in result

    def test_service_without_optional_fields_omits_them(self):
        """Vérifie l'absence des champs optionnels non définis."""
        config = ServiceConfig(
            description="Service minimal",
            exec_start="/usr/bin/minimal"
        )

        result = config.to_unit_file()

        assert "User=" not in result
        assert "Group=" not in result
        assert "WorkingDirectory=" not in result
        assert "Environment=" not in result
        assert "Restart=" not in result
        assert "RestartSec=" not in result

    def test_service_with_all_options(self):
        """Vérifie un service avec toutes les options."""
        config = ServiceConfig(
            description="Service complet",
            exec_start="/usr/bin/complete-daemon --config /etc/app.conf",
            type="forking",
            user="appuser",
            group="appgroup",
            working_directory="/var/lib/app",
            environment={"CONFIG": "/etc/app.conf"},
            restart="on-failure",
            restart_sec=5,
            wanted_by="multi-user.target"
        )

        result = config.to_unit_file()

        assert "Description=Service complet" in result
        assert "Type=forking" in result
        assert "ExecStart=/usr/bin/complete-daemon --config /etc/app.conf" \
            in result
        assert "User=appuser" in result
        assert "Group=appgroup" in result
        assert "WorkingDirectory=/var/lib/app" in result
        assert "Environment=CONFIG=/etc/app.conf" in result
        assert "Restart=on-failure" in result
        assert "RestartSec=5" in result


class TestServiceNameValidation:
    """Tests pour la validation des noms de service."""

    def test_rejet_caracteres_speciaux_dans_exec_start(self):
        """Vérifie le rejet de caractères spéciaux dans le nom extrait."""
        logger = MagicMock()
        executor = MagicMock()
        manager = LinuxServiceUnitManager(logger, executor)
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/cmd;evil"
        )
        result = manager.install_service_unit(config)
        assert result is False
        logger.log_error.assert_called_once()

    def test_rejet_nom_invalide_install_with_name(self):
        """Vérifie le rejet d'un nom invalide."""
        logger = MagicMock()
        executor = MagicMock()
        manager = LinuxServiceUnitManager(logger, executor)
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/test"
        )
        result = manager.install_service_unit_with_name(
            "../etc/passwd", config
        )
        assert result is False
        logger.log_error.assert_called_once()

    def test_rejet_nom_invalide_user_service(self):
        """Vérifie le rejet dans LinuxUserServiceUnitManager."""
        logger = MagicMock()
        executor = MagicMock()
        executor.reload_systemd.return_value = True
        manager = LinuxUserServiceUnitManager(logger, executor)
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/bad;name"
        )
        result = manager.install_service_unit(config)
        assert result is False
        logger.log_error.assert_called_once()

    def test_validation_start_service(self):
        """Vérifie la validation dans start_service."""
        logger = MagicMock()
        executor = MagicMock()
        manager = LinuxServiceUnitManager(logger, executor)
        with pytest.raises(ValueError, match="invalide"):
            manager.start_service("../evil")

    def test_validation_stop_service(self):
        """Vérifie la validation dans stop_service."""
        logger = MagicMock()
        executor = MagicMock()
        manager = LinuxServiceUnitManager(logger, executor)
        with pytest.raises(ValueError, match="invalide"):
            manager.stop_service("bad;name")

    def test_validation_enable_service(self):
        """Vérifie la validation dans enable_service."""
        logger = MagicMock()
        executor = MagicMock()
        manager = LinuxServiceUnitManager(logger, executor)
        with pytest.raises(ValueError, match="invalide"):
            manager.enable_service("$injection")


class TestServiceConfigValidation:
    """Tests pour la validation de ServiceConfig."""

    def test_rejet_type_invalide(self):
        """Vérifie le rejet d'un type de service inconnu."""
        with pytest.raises(ValueError, match="Type de service invalide"):
            ServiceConfig(
                description="Test",
                exec_start="/usr/bin/test",
                type="badtype"
            )

    @pytest.mark.parametrize("svc_type", [
        "simple", "exec", "forking", "oneshot",
        "dbus", "notify", "idle",
    ])
    def test_types_valides_acceptes(self, svc_type: str):
        """Vérifie l'acceptation de tous les types systemd valides."""
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/test",
            type=svc_type
        )
        assert config.type == svc_type

    def test_rejet_restart_invalide(self):
        """Vérifie le rejet d'une politique de redémarrage inconnue."""
        with pytest.raises(ValueError, match="redémarrage invalide"):
            ServiceConfig(
                description="Test",
                exec_start="/usr/bin/test",
                restart="bad-policy"
            )

    @pytest.mark.parametrize("restart", [
        "no", "always", "on-success", "on-failure",
        "on-abnormal", "on-abort", "on-watchdog",
    ])
    def test_restart_valides_acceptes(self, restart: str):
        """Vérifie l'acceptation de toutes les politiques de redémarrage."""
        config = ServiceConfig(
            description="Test",
            exec_start="/usr/bin/test",
            restart=restart
        )
        assert config.restart == restart

    def test_rejet_env_cle_avec_newline(self):
        """Vérifie le rejet d'une clé d'environnement avec newline."""
        with pytest.raises(ValueError, match="Clé d'environnement"):
            ServiceConfig(
                description="Test",
                exec_start="/usr/bin/test",
                environment={"BAD\nKEY": "value"}
            )

    def test_rejet_env_cle_avec_egal(self):
        """Vérifie le rejet d'une clé d'environnement avec '='."""
        with pytest.raises(ValueError, match="Clé d'environnement"):
            ServiceConfig(
                description="Test",
                exec_start="/usr/bin/test",
                environment={"BAD=KEY": "value"}
            )

    def test_rejet_env_valeur_avec_newline(self):
        """Vérifie le rejet d'une valeur d'environnement avec newline."""
        with pytest.raises(ValueError, match="retour à la ligne"):
            ServiceConfig(
                description="Test",
                exec_start="/usr/bin/test",
                environment={"KEY": "val\nue"}
            )


class TestWriteUnitFileAntiSymlink:
    """Tests pour la protection anti-symlink TOCTOU de _write_unit_file."""

    def test_write_refuse_lien_symbolique(self):
        """Vérifie que _write_unit_file refuse d'écrire sur un symlink."""
        temp_dir = tempfile.mkdtemp()
        try:
            logger = MagicMock()
            executor = MagicMock()
            manager = LinuxServiceUnitManager(logger, executor)
            manager.SYSTEMD_UNIT_PATH = temp_dir

            # Créer un symlink
            target = os.path.join(temp_dir, "target.txt")
            with open(target, "w") as f:
                f.write("original")
            link = os.path.join(temp_dir, "test.service")
            os.symlink(target, link)

            result = manager._write_unit_file(
                "test.service", "[Unit]\n"
            )

            assert result is False
            logger.log_error.assert_called_once()
            assert "symbolique" in logger.log_error.call_args[0][0]
        finally:
            shutil.rmtree(temp_dir)

    def test_write_cree_fichier_avec_permissions_644(self):
        """Vérifie que _write_unit_file crée le fichier en 0o644."""
        temp_dir = tempfile.mkdtemp()
        try:
            logger = MagicMock()
            executor = MagicMock()
            manager = LinuxServiceUnitManager(logger, executor)
            manager.SYSTEMD_UNIT_PATH = temp_dir

            result = manager._write_unit_file(
                "test.service", "[Unit]\nDescription=Test\n"
            )

            assert result is True
            path = os.path.join(temp_dir, "test.service")
            mode = os.stat(path).st_mode & 0o777
            assert mode == 0o644
            with open(path) as f:
                assert f.read() == "[Unit]\nDescription=Test\n"
        finally:
            shutil.rmtree(temp_dir)

    def test_remove_fichier_inexistant_succeeds(self):
        """Vérifie que _remove_unit_file réussit sur fichier inexistant."""
        temp_dir = tempfile.mkdtemp()
        try:
            logger = MagicMock()
            executor = MagicMock()
            manager = LinuxServiceUnitManager(logger, executor)
            manager.SYSTEMD_UNIT_PATH = temp_dir

            result = manager._remove_unit_file("nonexistent.service")
            assert result is True
        finally:
            shutil.rmtree(temp_dir)
