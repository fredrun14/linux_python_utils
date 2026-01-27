"""Tests pour le module integrity."""

import tempfile
from pathlib import Path

import pytest

from linux_python_utils.logging import FileLogger
from linux_python_utils.integrity import (
    calculate_checksum,
    SHA256IntegrityChecker
)


class TestCalculateChecksum:
    """Tests pour la fonction calculate_checksum."""

    def test_sha256(self, tmp_path):
        """Test du calcul SHA256."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = calculate_checksum(test_file)

        # SHA256 de "Hello, World!"
        assert len(checksum) == 64  # SHA256 = 64 caractères hex

    def test_different_content_different_checksum(self, tmp_path):
        """Test que des contenus différents donnent des checksums différents."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        checksum1 = calculate_checksum(file1)
        checksum2 = calculate_checksum(file2)

        assert checksum1 != checksum2

    def test_same_content_same_checksum(self, tmp_path):
        """Test que des contenus identiques donnent le même checksum."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Same content"
        file1.write_text(content)
        file2.write_text(content)

        checksum1 = calculate_checksum(file1)
        checksum2 = calculate_checksum(file2)

        assert checksum1 == checksum2

    def test_md5_algorithm(self, tmp_path):
        """Test avec algorithme MD5."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")

        checksum = calculate_checksum(test_file, algorithm='md5')

        assert len(checksum) == 32  # MD5 = 32 caractères hex

    def test_invalid_algorithm(self, tmp_path):
        """Test avec algorithme invalide."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")

        with pytest.raises(ValueError, match="non supporté"):
            calculate_checksum(test_file, algorithm='invalid')

    def test_file_not_found(self):
        """Test avec fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("/nonexistent/file.txt")


class TestSHA256IntegrityChecker:
    """Tests pour SHA256IntegrityChecker."""

    @pytest.fixture
    def logger(self, tmp_path):
        """Crée un logger pour les tests."""
        log_file = tmp_path / "test.log"
        return FileLogger(str(log_file))

    def test_verify_file_success(self, tmp_path, logger):
        """Test de vérification réussie d'un fichier."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        content = "Test content"
        source.write_text(content)
        dest.write_text(content)

        checker = SHA256IntegrityChecker(logger)

        assert checker.verify_file(str(source), str(dest)) is True

    def test_verify_file_failure(self, tmp_path, logger):
        """Test de vérification échouée d'un fichier."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("Content 1")
        dest.write_text("Content 2")

        checker = SHA256IntegrityChecker(logger)

        assert checker.verify_file(str(source), str(dest)) is False

    def test_verify_directory(self, tmp_path, logger):
        """Test de vérification d'un répertoire."""
        # Créer structure source
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Content 1")
        (source_dir / "file2.txt").write_text("Content 2")

        # Créer structure destination identique
        dest_dir = tmp_path / "dest" / "source"
        dest_dir.mkdir(parents=True)
        (dest_dir / "file1.txt").write_text("Content 1")
        (dest_dir / "file2.txt").write_text("Content 2")

        checker = SHA256IntegrityChecker(logger)

        assert checker.verify(str(source_dir), str(tmp_path / "dest")) is True

    def test_verify_missing_file(self, tmp_path, logger):
        """Test avec fichier manquant dans destination."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Content")

        dest_dir = tmp_path / "dest" / "source"
        dest_dir.mkdir(parents=True)
        # Pas de fichier dans dest

        checker = SHA256IntegrityChecker(logger)

        assert checker.verify(str(source_dir), str(tmp_path / "dest")) is False

    def test_get_checksum(self, tmp_path, logger):
        """Test de la méthode get_checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")

        checker = SHA256IntegrityChecker(logger)
        checksum = checker.get_checksum(str(test_file))

        assert len(checksum) == 64
