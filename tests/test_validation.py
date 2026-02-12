"""Tests pour le module validation."""

from unittest.mock import patch

import pytest

from linux_python_utils.validation import PathChecker


class TestPathChecker:
    """Tests pour PathChecker."""

    def test_validate_accessible_paths(self, tmp_path):
        """Vérifie que la validation passe pour des chemins accessibles."""
        checker = PathChecker([str(tmp_path / "file.txt")])
        checker.validate()

    def test_validate_nonexistent_directory(self):
        """Vérifie ValueError si le répertoire parent n'existe pas."""
        checker = PathChecker(["/nonexistent/dir/file.log"])
        with pytest.raises(ValueError, match="n'existe pas"):
            checker.validate()

    @patch(
        'linux_python_utils.validation.path_checker.os.access',
        return_value=False
    )
    @patch(
        'linux_python_utils.validation.path_checker.os.path.exists',
        return_value=True
    )
    def test_validate_no_write_permission(self, mock_exists, mock_access):
        """Vérifie PermissionError si l'écriture est impossible."""
        checker = PathChecker(["/restricted/dir/file.log"])
        with pytest.raises(PermissionError, match="Permissions insuffisantes"):
            checker.validate()

    def test_validate_multiple_paths(self, tmp_path):
        """Vérifie la validation avec plusieurs chemins valides."""
        paths = [
            str(tmp_path / "file1.txt"),
            str(tmp_path / "file2.txt"),
        ]
        checker = PathChecker(paths)
        checker.validate()

    def test_validate_stops_at_first_error(self, tmp_path):
        """Vérifie que la validation s'arrête à la première erreur."""
        paths = [
            str(tmp_path / "valid.txt"),
            "/nonexistent/dir/file.log",
        ]
        checker = PathChecker(paths)
        with pytest.raises(ValueError):
            checker.validate()
