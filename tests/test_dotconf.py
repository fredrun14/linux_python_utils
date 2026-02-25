"""Tests unitaires pour le module dotconf."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from linux_python_utils.dotconf import (
    LinuxIniConfigManager,
    ValidatedSection,
    build_validators,
    parse_validator,
)
from linux_python_utils.logging import FileLogger


# Fixtures


@pytest.fixture
def temp_log_file():
    """Crée un fichier de log temporaire."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_ini_file():
    """Crée un fichier INI temporaire."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def logger(temp_log_file):
    """Crée un logger pour les tests."""
    return FileLogger(temp_log_file)


@pytest.fixture
def manager(logger):
    """Crée un gestionnaire INI pour les tests."""
    return LinuxIniConfigManager(logger)


# Section de test


@dataclass(frozen=True)
class CommandsSectionFixture(ValidatedSection):
    """Section de test pour les commandes."""

    upgrade_type: str = "default"
    download_updates: str = "yes"
    apply_updates: str = "yes"
    random_sleep: str = "300"

    @staticmethod
    def section_name() -> str:
        return "commands"


@dataclass(frozen=True)
class MainSectionFixture(ValidatedSection):
    """Section de test pour main."""

    fastestmirror: str = "true"
    max_parallel_downloads: str = "10"

    @staticmethod
    def section_name() -> str:
        return "main"


# Tests parse_validator


class TestParseValidator:
    """Tests pour la fonction parse_validator."""

    def test_parse_list_validator(self):
        """Teste le parsing d'une liste de valeurs."""
        result = parse_validator(["yes", "no"])
        assert result == ["yes", "no"]

    def test_parse_non_list_raises(self):
        """Teste qu'un string lève une exception."""
        with pytest.raises(ValueError, match="Format de validateur invalide"):
            parse_validator("lambda x: x.isdigit()")

    def test_parse_invalid_validator_raises(self):
        """Teste qu'un validateur invalide lève une exception."""
        with pytest.raises(ValueError, match="Format de validateur invalide"):
            parse_validator("invalid string")


class TestBuildValidators:
    """Tests pour la fonction build_validators."""

    def test_build_list_validators(self):
        """Teste la construction d'un dictionnaire de listes."""
        validators_dict = {
            "field1": ["opt1", "opt2"],
            "field2": ["a", "b", "c"],
        }
        result = build_validators(validators_dict)

        assert result["field1"] == ["opt1", "opt2"]
        assert result["field2"] == ["a", "b", "c"]


# Tests ValidatedSection


class TestValidatedSection:
    """Tests pour ValidatedSection."""

    def setup_method(self):
        """Configure les validators avant chaque test."""
        CommandsSectionFixture.set_validators({
            "upgrade_type": ["default", "security"],
            "download_updates": ["yes", "no"],
            "apply_updates": ["yes", "no"],
            "random_sleep": lambda x: x.isdigit() and 0 <= int(x) <= 86400,
        })

    def teardown_method(self):
        """Nettoie les validators après chaque test."""
        CommandsSectionFixture.clear_validators()

    def test_create_valid_section(self):
        """Teste la création d'une section valide."""
        section = CommandsSectionFixture(
            upgrade_type="default",
            download_updates="yes",
            apply_updates="no",
            random_sleep="600",
        )
        assert section.upgrade_type == "default"
        assert section.download_updates == "yes"
        assert section.apply_updates == "no"
        assert section.random_sleep == "600"

    def test_create_with_defaults(self):
        """Teste la création avec les valeurs par défaut."""
        section = CommandsSectionFixture()
        assert section.upgrade_type == "default"
        assert section.download_updates == "yes"

    def test_invalid_list_value_raises(self):
        """Teste qu'une valeur invalide dans une liste lève une exception."""
        with pytest.raises(ValueError, match="upgrade_type='invalid' invalide"):
            CommandsSectionFixture(upgrade_type="invalid")

    def test_invalid_lambda_value_raises(self):
        """Teste qu'une valeur invalide pour un lambda lève une exception."""
        with pytest.raises(ValueError, match="random_sleep='abc' échoue"):
            CommandsSectionFixture(random_sleep="abc")

    def test_lambda_out_of_range_raises(self):
        """Teste qu'une valeur hors limites lève une exception."""
        with pytest.raises(ValueError, match="random_sleep='100000' échoue"):
            CommandsSectionFixture(random_sleep="100000")

    def test_section_name(self):
        """Teste que section_name retourne le bon nom."""
        section = CommandsSectionFixture()
        assert section.section_name() == "commands"

    def test_to_dict(self):
        """Teste la conversion en dictionnaire."""
        section = CommandsSectionFixture(
            upgrade_type="security",
            download_updates="no",
        )
        result = section.to_dict()
        assert result["upgrade_type"] == "security"
        assert result["download_updates"] == "no"
        assert "apply_updates" in result
        assert "random_sleep" in result

    def test_from_dict(self):
        """Teste la création depuis un dictionnaire."""
        data = {
            "upgrade_type": "security",
            "download_updates": "no",
            "apply_updates": "yes",
            "random_sleep": "100",
        }
        section = CommandsSectionFixture.from_dict(data)
        assert section.upgrade_type == "security"
        assert section.download_updates == "no"

    def test_immutability(self):
        """Teste que la section est immuable (frozen)."""
        section = CommandsSectionFixture()
        with pytest.raises(AttributeError):
            section.upgrade_type = "security"

    def test_without_validators(self):
        """Teste la création sans validators (pas de validation)."""
        CommandsSectionFixture.clear_validators()
        section = CommandsSectionFixture(upgrade_type="anything")
        assert section.upgrade_type == "anything"


# Tests LinuxIniConfigManager


class TestLinuxIniConfigManager:
    """Tests pour LinuxIniConfigManager."""

    def setup_method(self):
        """Configure les validators."""
        CommandsSectionFixture.set_validators({
            "upgrade_type": ["default", "security"],
            "download_updates": ["yes", "no"],
            "apply_updates": ["yes", "no"],
            "random_sleep": lambda x: x.isdigit() and 0 <= int(x) <= 86400,
        })
        MainSectionFixture.set_validators({
            "fastestmirror": ["true", "false"],
            "max_parallel_downloads": lambda x: x.isdigit() and 1 <= int(x) <= 20,
        })

    def teardown_method(self):
        """Nettoie les validators."""
        CommandsSectionFixture.clear_validators()
        MainSectionFixture.clear_validators()

    def test_write_and_read_section(self, manager, temp_ini_file):
        """Teste l'écriture et la lecture d'une section."""
        path = Path(temp_ini_file)
        section = CommandsSectionFixture(upgrade_type="security")

        manager.write_section(path, section)
        result = manager.read(path)

        assert "commands" in result
        assert result["commands"]["upgrade_type"] == "security"

    def test_read_nonexistent_file_raises(self, manager):
        """Teste que la lecture d'un fichier inexistant lève une exception."""
        with pytest.raises(FileNotFoundError):
            manager.read(Path("/nonexistent/file.conf"))

    def test_update_section_with_changes(self, manager, temp_ini_file):
        """Teste la mise à jour d'une section avec modifications."""
        path = Path(temp_ini_file)
        section1 = CommandsSectionFixture(upgrade_type="default")
        manager.write_section(path, section1)

        section2 = CommandsSectionFixture(upgrade_type="security")
        updated = manager.update_section(path, section2)

        assert updated is True
        result = manager.read(path)
        assert result["commands"]["upgrade_type"] == "security"

    def test_update_section_no_changes(self, manager, temp_ini_file):
        """Teste la mise à jour sans modifications."""
        path = Path(temp_ini_file)
        section = CommandsSectionFixture()
        manager.write_section(path, section)

        updated = manager.update_section(path, section)
        assert updated is False

    def test_section_to_ini(self, manager):
        """Teste la génération du contenu INI d'une section."""
        section = CommandsSectionFixture(upgrade_type="security")
        ini_content = manager.section_to_ini(section)

        assert "[commands]" in ini_content
        assert "upgrade_type = security" in ini_content

    def test_multiple_sections(self, manager, temp_ini_file):
        """Teste l'écriture de plusieurs sections."""
        path = Path(temp_ini_file)

        section1 = CommandsSectionFixture(upgrade_type="security")
        section2 = MainSectionFixture(fastestmirror="true")

        manager.write_section(path, section1)
        manager.write_section(path, section2)

        result = manager.read(path)
        assert "commands" in result
        assert "main" in result
        assert result["commands"]["upgrade_type"] == "security"
        assert result["main"]["fastestmirror"] == "true"

    def test_write_config(self, manager, temp_ini_file):
        """Teste write() avec un IniConfig complet."""
        from linux_python_utils.dotconf.base import IniConfig
        from dataclasses import dataclass

        path = Path(temp_ini_file)

        class SimpleConfig(IniConfig):
            def sections(self):
                return [CommandsSectionFixture(upgrade_type="security")]

            def to_ini(self) -> str:
                return manager.config_to_ini(self)

            @classmethod
            def from_file(cls, path):
                raise NotImplementedError

        config = SimpleConfig()
        manager.write(path, config)
        result = manager.read(path)
        assert "commands" in result
        assert result["commands"]["upgrade_type"] == "security"

    def test_config_to_ini(self, manager):
        """Teste config_to_ini() avec plusieurs sections."""
        from linux_python_utils.dotconf.base import IniConfig

        class SimpleConfig(IniConfig):
            def sections(self):
                return [
                    CommandsSectionFixture(upgrade_type="security"),
                    MainSectionFixture(fastestmirror="true"),
                ]

            def to_ini(self) -> str:
                return manager.config_to_ini(self)

            @classmethod
            def from_file(cls, path):
                raise NotImplementedError

        config = SimpleConfig()
        ini = manager.config_to_ini(config)
        assert "[commands]" in ini
        assert "[main]" in ini
        assert "upgrade_type = security" in ini

    def test_update_section_fichier_inexistant(self, manager, tmp_path):
        """update_section() sur un fichier inexistant cree la section."""
        path = tmp_path / "new_config.conf"
        section = CommandsSectionFixture(upgrade_type="security")
        updated = manager.update_section(path, section)
        assert updated is True
        result = manager.read(path)
        assert result["commands"]["upgrade_type"] == "security"


class TestValidatedSectionEdgeCases:
    """Tests pour les cas limites de ValidatedSection."""

    def test_section_name_not_implemented(self):
        """section_name() leve NotImplementedError si non redefini."""
        import pytest
        with pytest.raises(NotImplementedError):
            ValidatedSection.section_name()

    def test_private_field_skipped_in_validation(self):
        """Les champs prives (commencant par _) sont ignores."""
        from dataclasses import dataclass, field as dataclass_field

        @dataclass(frozen=True)
        class SectionWithPrivate(ValidatedSection):
            public: str = "val"
            _private: str = dataclass_field(default="priv", init=False)

            @staticmethod
            def section_name() -> str:
                return "test"

        SectionWithPrivate.set_validators({
            "public": ["val", "other"],
        })
        try:
            section = SectionWithPrivate()
            assert section.public == "val"
        finally:
            SectionWithPrivate.clear_validators()
