"""Tests pour le module systemd.service."""

import pytest

from linux_python_utils.systemd.base import ServiceConfig


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
