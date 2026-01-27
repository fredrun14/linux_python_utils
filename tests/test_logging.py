"""Tests pour le module logging."""

import tempfile
from pathlib import Path

import pytest

from linux_python_utils.logging import Logger, FileLogger


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
