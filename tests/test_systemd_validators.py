"""Tests pour le module systemd.validators."""

import pytest

from linux_python_utils.systemd.validators import (
    validate_unit_name,
    validate_service_name,
)


class TestValidateUnitName:
    """Tests pour validate_unit_name."""

    @pytest.mark.parametrize("name", [
        "backup",
        "my-service",
        "my_service",
        "my.unit",
        "sys:name",
        "A1",
        "backup-daily_2",
    ])
    def test_noms_valides(self, name: str):
        """Vérifie l'acceptation de noms d'unités valides."""
        assert validate_unit_name(name) == name

    def test_rejet_nom_vide(self):
        """Vérifie le rejet d'un nom vide."""
        with pytest.raises(ValueError, match="vide"):
            validate_unit_name("")

    def test_rejet_traversee_chemin(self):
        """Vérifie le rejet de traversée de chemin."""
        with pytest.raises(ValueError, match="traversée"):
            validate_unit_name("../etc/passwd")

    def test_rejet_slash(self):
        """Vérifie le rejet de slash."""
        with pytest.raises(ValueError, match="traversée"):
            validate_unit_name("foo/bar")

    def test_rejet_injection_point_virgule(self):
        """Vérifie le rejet d'injection de commande."""
        with pytest.raises(ValueError, match="invalide"):
            validate_unit_name("name;cmd")

    def test_rejet_injection_dollar(self):
        """Vérifie le rejet d'injection via $()."""
        with pytest.raises(ValueError, match="invalide"):
            validate_unit_name("name$(cmd)")

    def test_rejet_espaces(self):
        """Vérifie le rejet d'espaces."""
        with pytest.raises(ValueError, match="invalide"):
            validate_unit_name("name with spaces")

    def test_rejet_debut_non_alphanum(self):
        """Vérifie le rejet d'un nom commençant par un tiret."""
        with pytest.raises(ValueError, match="invalide"):
            validate_unit_name("-backup")


class TestValidateServiceName:
    """Tests pour validate_service_name."""

    @pytest.mark.parametrize("name", [
        "backup",
        "my-service",
        "my_service",
        "A1",
        "backup-daily_2",
    ])
    def test_noms_valides(self, name: str):
        """Vérifie l'acceptation de noms de services valides."""
        assert validate_service_name(name) == name

    def test_rejet_nom_vide(self):
        """Vérifie le rejet d'un nom vide."""
        with pytest.raises(ValueError, match="vide"):
            validate_service_name("")

    def test_rejet_traversee_chemin(self):
        """Vérifie le rejet de traversée de chemin."""
        with pytest.raises(ValueError, match="traversée"):
            validate_service_name("../etc/passwd")

    def test_rejet_slash(self):
        """Vérifie le rejet de slash."""
        with pytest.raises(ValueError, match="traversée"):
            validate_service_name("foo/bar")

    def test_rejet_point(self):
        """Vérifie le rejet de points (contrairement à unit_name)."""
        with pytest.raises(ValueError, match="invalide"):
            validate_service_name("my.service")

    def test_rejet_deux_points(self):
        """Vérifie le rejet de deux-points."""
        with pytest.raises(ValueError, match="invalide"):
            validate_service_name("sys:name")

    def test_rejet_caracteres_speciaux(self):
        """Vérifie le rejet de caractères spéciaux."""
        with pytest.raises(ValueError, match="invalide"):
            validate_service_name("name;cmd")
