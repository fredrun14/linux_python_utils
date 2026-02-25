"""Tests pour le module logging."""

import tempfile
from pathlib import Path

import pytest

from linux_python_utils.logging import Logger, FileLogger
from unittest.mock import MagicMock


class TestFileLogger:
    """Tests pour FileLogger."""

    def test_implements_logger_interface(self, tmp_path):
        """Vérifie que FileLogger implémente l'interface Logger."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        assert isinstance(logger, Logger)

    def test_log_info(self, tmp_path):
        """Test du logging info."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        logger.log_info("Test message")

        content = log_file.read_text()
        assert "INFO" in content
        assert "Test message" in content

    def test_log_warning(self, tmp_path):
        """Test du logging warning."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        logger.log_warning("Warning message")

        content = log_file.read_text()
        assert "WARNING" in content
        assert "Warning message" in content

    def test_log_error(self, tmp_path):
        """Test du logging error."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        logger.log_error("Error message")

        content = log_file.read_text()
        assert "ERROR" in content
        assert "Error message" in content

    def test_creates_log_directory(self, tmp_path):
        """Test que le répertoire de log est créé si nécessaire."""
        log_file = tmp_path / "subdir" / "test.log"

        logger = FileLogger(str(log_file))
        logger.log_info("Test")

        assert log_file.exists()

    def test_config_from_dict(self, tmp_path):
        """Test de la configuration depuis un dictionnaire."""
        log_file = tmp_path / "test.log"
        config = {
            "logging": {
                "level": "DEBUG",
                "format": "%(levelname)s - %(message)s"
            }
        }

        logger = FileLogger(str(log_file), config=config)
        logger.log_info("Test")

        content = log_file.read_text()
        assert "INFO - Test" in content

    def test_utf8_encoding(self, tmp_path):
        """Test de l'encodage UTF-8."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        logger.log_info("Message avec accents: éàü")

        content = log_file.read_text(encoding='utf-8')
        assert "éàü" in content

    def test_log_to_file_direct(self, tmp_path):
        """Test de l'écriture directe sans formatage."""
        log_file = tmp_path / "test.log"
        logger = FileLogger(str(log_file))

        logger.log_to_file("Direct message")

        content = log_file.read_text()
        assert "Direct message" in content


class TestFileLoggerConsole:
    """Tests pour FileLogger avec sortie console et handlers dupliqués."""

    def test_console_output_active(self, tmp_path):
        """FileLogger avec console_output=True crée un StreamHandler."""
        import logging
        log_file = str(tmp_path / "console.log")
        logger = FileLogger(log_file, console_output=True)
        # Vérifie qu'il y a 2 handlers (fichier + console)
        assert len(logger.logger.handlers) == 2
        logger.log_info("Test console")

    def test_logger_handler_existant_reutilise(self, tmp_path):
        """Crée deux FileLogger sur le même fichier : handler réutilisé."""
        log_file = str(tmp_path / "shared.log")
        # Premier logger : crée les handlers
        logger1 = FileLogger(log_file)
        handler_count_1 = len(logger1.logger.handlers)
        # Deuxième logger sur le même fichier : doit réutiliser
        logger2 = FileLogger(log_file)
        # Le handler est récupéré depuis les handlers existants
        assert logger2.handler is not None
        logger2.log_info("Test handler réutilisé")

    def test_config_objet_type_erreur(self, tmp_path):
        """FileLogger avec config dont get() lève TypeError."""
        log_file = str(tmp_path / "type_err.log")

        class ConfigTypeError:
            """Config dont get() lève TypeError pour les clés pointées."""
            def get(self, key, default=None):
                # Simule un objet qui ne gère pas les clés en notation pointée
                if "." in key:
                    raise TypeError("Clé pointée non supportée")
                if key == "logging":
                    return {"level": "INFO", "format": "%(message)s"}
                return default

        config = ConfigTypeError()
        logger = FileLogger(log_file, config=config)
        logger.log_info("Test avec TypeError")
        content = (tmp_path / "type_err.log").read_text(encoding="utf-8")
        assert "Test avec TypeError" in content


class TestSecurityLogger:
    """Tests pour SecurityLogger et SecurityEvent."""

    def test_log_event_info(self):
        """log_event avec severity='info' appelle log_info."""
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            resource="/api/login",
            severity="info",
        )
        sec_logger.log_event(event)
        mock_logger.log_info.assert_called_once()
        call_arg = mock_logger.log_info.call_args[0][0]
        assert "auth.success" in call_arg

    def test_log_event_warning(self):
        """log_event avec severity='warning' appelle log_warning."""
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_HIT,
            resource="/api/upload",
            severity="warning",
        )
        sec_logger.log_event(event)
        mock_logger.log_warning.assert_called_once()

    def test_log_event_error(self):
        """log_event avec severity='error' appelle log_error."""
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.ACCESS_DENIED,
            resource="/admin",
            severity="error",
        )
        sec_logger.log_event(event)
        mock_logger.log_error.assert_called_once()

    def test_log_event_critical(self):
        """log_event avec severity='critical' appelle log_error."""
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            resource="/hack",
            severity="critical",
        )
        sec_logger.log_event(event)
        mock_logger.log_error.assert_called_once()

    def test_log_event_avec_user_id(self):
        """log_event inclut user_id dans le payload JSON."""
        import json
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.CONFIG_CHANGE,
            resource="/etc/app.conf",
            severity="warning",
            user_id="admin",
        )
        sec_logger.log_event(event)
        call_arg = mock_logger.log_warning.call_args[0][0]
        payload = json.loads(call_arg)
        assert payload["user_id"] == "admin"

    def test_log_event_sans_user_id_pas_dans_payload(self):
        """log_event sans user_id n'inclut pas user_id dans le payload."""
        import json
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_EXPORT,
            severity="info",
        )
        sec_logger.log_event(event)
        call_arg = mock_logger.log_info.call_args[0][0]
        payload = json.loads(call_arg)
        assert "user_id" not in payload

    def test_log_event_avec_details(self):
        """log_event inclut les détails dans le payload JSON."""
        import json
        from linux_python_utils.logging.security_logger import (
            SecurityLogger, SecurityEvent, SecurityEventType
        )
        mock_logger = MagicMock()
        sec_logger = SecurityLogger(mock_logger)
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_MODIFICATION,
            resource="/db/users",
            details={"table": "users", "rows": 5},
            severity="info",
        )
        sec_logger.log_event(event)
        call_arg = mock_logger.log_info.call_args[0][0]
        payload = json.loads(call_arg)
        assert payload["details"]["table"] == "users"

    def test_config_sans_methode_get(self, tmp_path):
        """FileLogger avec config sans methode get() utilise les valeurs par defaut."""
        log_file = str(tmp_path / "test.log")

        class ConfigSansGet:
            """Config sans methode get()."""
            pass

        logger = FileLogger(log_file, config=ConfigSansGet())
        logger.log_info("Test sans get")
        content = (tmp_path / "test.log").read_text(encoding="utf-8")
        assert "Test sans get" in content
