"""Tests pour linux_python_utils.cli.base."""
import argparse
import pytest
from linux_python_utils.cli.base import CliApplication, CliCommand


class ConcreteCommand(CliCommand):
    """Commande concrète pour les tests."""

    def __init__(self, cmd_name: str = "test-cmd") -> None:
        self._name = cmd_name
        self.execute_called = False
        self.last_args = None

    @property
    def name(self) -> str:
        return self._name

    def register(self, subparsers) -> None:
        p = subparsers.add_parser(self._name, help="Test command")
        p.add_argument("--flag", default="default")

    def execute(self, args: argparse.Namespace) -> None:
        self.execute_called = True
        self.last_args = args


class TestCliCommand:
    def test_cli_command_abc_ne_peut_pas_etre_instancie(self):
        with pytest.raises(TypeError):
            CliCommand()  # type: ignore

    def test_concrete_command_a_un_nom(self):
        cmd = ConcreteCommand("my-cmd")
        assert cmd.name == "my-cmd"


class TestCliApplication:
    def test_run_dispatche_vers_la_bonne_commande(self, monkeypatch):
        cmd_a = ConcreteCommand("cmd-a")
        cmd_b = ConcreteCommand("cmd-b")
        app = CliApplication("test", "Test app", [cmd_a, cmd_b])
        monkeypatch.setattr("sys.argv", ["test", "cmd-b"])
        app.run()
        assert cmd_b.execute_called
        assert not cmd_a.execute_called

    def test_run_passe_les_arguments_a_la_commande(self, monkeypatch):
        cmd = ConcreteCommand("cmd-a")
        app = CliApplication("test", "Test app", [cmd])
        monkeypatch.setattr("sys.argv", ["test", "cmd-a", "--flag", "valeur"])
        app.run()
        assert cmd.last_args.flag == "valeur"

    def test_run_sans_commande_leve_system_exit(self, monkeypatch):
        cmd = ConcreteCommand("cmd-a")
        app = CliApplication("test", "Test app", [cmd])
        monkeypatch.setattr("sys.argv", ["test"])
        with pytest.raises(SystemExit):
            app.run()

    def test_run_commande_inconnue_leve_system_exit(self, monkeypatch):
        cmd = ConcreteCommand("cmd-a")
        app = CliApplication("test", "Test app", [cmd])
        monkeypatch.setattr("sys.argv", ["test", "inexistant"])
        with pytest.raises(SystemExit):
            app.run()
