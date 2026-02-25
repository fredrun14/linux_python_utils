"""Tests pour le module validation."""

from unittest.mock import patch

import pytest

from linux_python_utils.validation import PathChecker, PathCheckerPermission


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


class TestPathCheckerPermission:
    """Tests pour PathCheckerPermission."""

    def test_validate_accessible_paths(self, tmp_path):
        """Vérifie que la validation passe pour un répertoire accessible."""
        checker = PathCheckerPermission([str(tmp_path / "file.txt")])
        checker.validate()

    def test_validate_nonexistent_directory(self):
        """Vérifie ValueError si le répertoire parent n'existe pas."""
        checker = PathCheckerPermission(["/nonexistent/dir/file.log"])
        with pytest.raises(ValueError, match="n'existe pas"):
            checker.validate()

    def test_validate_no_write_permission(self, tmp_path):
        """Vérifie PermissionError si l'écriture est impossible."""
        checker = PathCheckerPermission([str(tmp_path / "file.log")])
        with patch(
            "linux_python_utils.validation.path_checker_permission"
            ".os.access",
            return_value=False,
        ):
            with pytest.raises(
                PermissionError, match="Permissions insuffisantes"
            ):
                checker.validate()


class TestPathCheckerWorldWritable:
    """Tests pour PathCheckerWorldWritable."""

    def test_fichier_non_world_writable_valide(self, tmp_path):
        """validate() ne lève pas d'exception si non world-writable."""
        from linux_python_utils.validation.path_checker_world_writable import (
            PathCheckerWorldWritable
        )
        f = tmp_path / "secure.conf"
        f.write_text("config")
        import os
        os.chmod(str(f), 0o644)
        checker = PathCheckerWorldWritable(str(f))
        checker.validate()  # Ne doit pas lever d'exception

    def test_fichier_world_writable_leve_permission_error(self, tmp_path):
        """validate() lève PermissionError si le fichier est world-writable."""
        from linux_python_utils.validation.path_checker_world_writable import (
            PathCheckerWorldWritable
        )
        f = tmp_path / "dangereux.conf"
        f.write_text("config")
        import os
        os.chmod(str(f), 0o666)  # world-writable
        checker = PathCheckerWorldWritable(str(f))
        with pytest.raises(PermissionError, match="world-writable"):
            checker.validate()

    def test_fichier_inexistant_leve_file_not_found(self, tmp_path):
        """validate() lève FileNotFoundError si le fichier n'existe pas."""
        from linux_python_utils.validation.path_checker_world_writable import (
            PathCheckerWorldWritable
        )
        checker = PathCheckerWorldWritable(
            str(tmp_path / "inexistant.conf")
        )
        with pytest.raises(FileNotFoundError, match="introuvable"):
            checker.validate()
