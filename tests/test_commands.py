"""Tests pour le module commands."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from linux_python_utils.commands import (
    CommandBuilder,
    CommandResult,
    LinuxCommandExecutor,
)
from linux_python_utils.logging.base import Logger


# --- Tests CommandResult ---


class TestCommandResult:
    """Tests pour la dataclass CommandResult."""

    def test_creation_avec_tous_les_champs(self):
        """Test de la création avec tous les champs."""
        result = CommandResult(
            command=["ls", "-la"],
            return_code=0,
            stdout="fichier.txt",
            stderr="",
            success=True,
            duration=0.5,
        )
        assert result.command == ["ls", "-la"]
        assert result.return_code == 0
        assert result.stdout == "fichier.txt"
        assert result.stderr == ""
        assert result.success is True
        assert result.duration == 0.5

    def test_frozen(self):
        """Test que la dataclass est immuable."""
        result = CommandResult(
            command=["ls"],
            return_code=0,
            stdout="",
            stderr="",
            success=True,
            duration=0.0,
        )
        with pytest.raises(AttributeError):
            result.return_code = 1

    def test_success_true_quand_code_zero(self):
        """Test success=True quand return_code est 0."""
        result = CommandResult(
            command=["echo"],
            return_code=0,
            stdout="",
            stderr="",
            success=True,
            duration=0.1,
        )
        assert result.success is True

    def test_success_false_quand_code_non_zero(self):
        """Test success=False quand return_code est non-zéro."""
        result = CommandResult(
            command=["false"],
            return_code=1,
            stdout="",
            stderr="erreur",
            success=False,
            duration=0.1,
        )
        assert result.success is False
        assert result.return_code == 1


# --- Tests CommandBuilder ---


class TestCommandBuilder:
    """Tests pour le constructeur fluent CommandBuilder."""

    def test_build_programme_seul(self):
        """Test de build avec le programme seul."""
        cmd = CommandBuilder("ls").build()
        assert cmd == ["ls"]

    def test_with_flag(self):
        """Test d'ajout d'un flag simple."""
        cmd = (
            CommandBuilder("ls")
            .with_flag("-l")
            .build()
        )
        assert cmd == ["ls", "-l"]

    def test_with_options(self):
        """Test d'ajout d'une liste d'options."""
        cmd = (
            CommandBuilder("rsync")
            .with_options(["-av", "--delete"])
            .build()
        )
        assert cmd == ["rsync", "-av", "--delete"]

    def test_with_option_cle_valeur(self):
        """Test d'ajout d'une option clé=valeur."""
        cmd = (
            CommandBuilder("borg")
            .with_option("--compression", "lz4")
            .build()
        )
        assert cmd == ["borg", "--compression=lz4"]

    def test_with_option_if_condition_vraie(self):
        """Test d'ajout conditionnel avec condition vraie."""
        cmd = (
            CommandBuilder("rsync")
            .with_option_if(
                "--exclude-from", "/tmp/exclude",
                condition=True,
            )
            .build()
        )
        assert cmd == [
            "rsync", "--exclude-from=/tmp/exclude"
        ]

    def test_with_option_if_condition_fausse(self):
        """Test d'ajout conditionnel avec condition fausse."""
        cmd = (
            CommandBuilder("rsync")
            .with_option_if(
                "--exclude-from", "/tmp/exclude",
                condition=False,
            )
            .build()
        )
        assert cmd == ["rsync"]

    def test_with_option_if_valeur_none(self):
        """Test d'ajout conditionnel avec valeur None."""
        cmd = (
            CommandBuilder("rsync")
            .with_option_if(
                "--exclude-from", None,
                condition=True,
            )
            .build()
        )
        assert cmd == ["rsync"]

    def test_with_args(self):
        """Test d'ajout d'arguments positionnels."""
        cmd = (
            CommandBuilder("cp")
            .with_args(["/src", "/dest"])
            .build()
        )
        assert cmd == ["cp", "/src", "/dest"]

    def test_chainage_complet(self):
        """Test du chaînage fluent complet."""
        cmd = (
            CommandBuilder("rsync")
            .with_options(["-av", "--delete"])
            .with_option("--compress-level", "3")
            .with_flag("--stats")
            .with_args(["/src/", "/dest/"])
            .build()
        )
        assert cmd == [
            "rsync", "-av", "--delete",
            "--compress-level=3", "--stats",
            "/src/", "/dest/",
        ]

    def test_programme_vide_leve_erreur(self):
        """Test qu'un programme vide lève ValueError."""
        with pytest.raises(ValueError):
            CommandBuilder("")

    def test_programme_espaces_leve_erreur(self):
        """Test qu'un programme d'espaces lève ValueError."""
        with pytest.raises(ValueError):
            CommandBuilder("   ")


# --- Tests LinuxCommandExecutor.run ---


class TestLinuxCommandExecutorRun:
    """Tests pour la méthode run() de LinuxCommandExecutor."""

    def setup_method(self):
        """Initialise les mocks pour chaque test."""
        self.mock_logger = MagicMock(spec=Logger)
        self.executor = LinuxCommandExecutor(
            logger=self.mock_logger,
        )

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_commande_reussie(self, mock_run):
        """Test d'une commande réussie."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="sortie",
            stderr="",
        )
        result = self.executor.run(["echo", "test"])

        assert result.success is True
        assert result.return_code == 0
        assert result.stdout == "sortie"
        assert result.stderr == ""
        assert result.command == ["echo", "test"]
        assert result.duration >= 0

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_commande_echouee(self, mock_run):
        """Test d'une commande échouée."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="erreur",
        )
        result = self.executor.run(["false"])

        assert result.success is False
        assert result.return_code == 1
        assert result.stderr == "erreur"

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_timeout(self, mock_run):
        """Test du timeout lors de l'exécution."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["sleep", "100"], timeout=5,
        )
        result = self.executor.run(
            ["sleep", "100"], timeout=5,
        )

        assert result.success is False
        assert result.return_code == -1
        self.mock_logger.log_error.assert_called_once()

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_commande_introuvable(self, mock_run):
        """Test avec une commande introuvable."""
        mock_run.side_effect = FileNotFoundError(
            "No such file or directory: 'inexistant'"
        )
        result = self.executor.run(["inexistant"])

        assert result.success is False
        assert result.return_code == -1
        self.mock_logger.log_error.assert_called_once()

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_log_commande(self, mock_run):
        """Test que la commande est loguée."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="",
        )
        self.executor.run(["ls", "-la"])

        self.mock_logger.log_info.assert_called_once()
        call_args = (
            self.mock_logger.log_info.call_args[0][0]
        )
        assert "ls -la" in call_args

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_avec_cwd(self, mock_run):
        """Test de l'exécution avec répertoire de travail."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="",
        )
        self.executor.run(["ls"], cwd="/tmp")

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == "/tmp"

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_run_sans_logger(self, mock_run):
        """Test de l'exécution sans logger."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr="",
        )
        executor = LinuxCommandExecutor()
        result = executor.run(["echo", "test"])

        assert result.success is True
        assert result.stdout == "ok"


# --- Tests LinuxCommandExecutor.run_streaming ---


class TestLinuxCommandExecutorRunStreaming:
    """Tests pour la méthode run_streaming()."""

    def setup_method(self):
        """Initialise les mocks pour chaque test."""
        self.mock_logger = MagicMock(spec=Logger)
        self.executor = LinuxCommandExecutor(
            logger=self.mock_logger,
        )

    def _make_mock_proc(
        self, stdout_lines, stderr="", returncode=0,
    ):
        """Crée un mock de Popen configuré."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(stdout_lines)
        mock_proc.stderr.read.return_value = stderr
        mock_proc.returncode = returncode
        mock_proc.wait.return_value = None
        return mock_proc

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_streaming_capture_sortie(self, mock_popen):
        """Test de la capture de sortie en streaming."""
        mock_popen.return_value = self._make_mock_proc(
            ["ligne1\n", "ligne2\n"],
        )
        result = self.executor.run_streaming(["cmd"])

        assert result.success is True
        assert result.stdout == "ligne1\nligne2"

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_streaming_log_chaque_ligne(self, mock_popen):
        """Test que chaque ligne est loguée."""
        mock_popen.return_value = self._make_mock_proc(
            ["ligne1\n", "ligne2\n", "ligne3\n"],
        )
        self.executor.run_streaming(["cmd"])

        # 1 appel pour "Exécution (streaming)" + 3 lignes
        assert self.mock_logger.log_info.call_count == 4

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_streaming_timeout(self, mock_popen):
        """Test du timeout en mode streaming."""
        mock_proc = self._make_mock_proc(
            ["partiel\n"],
        )
        mock_proc.wait.side_effect = [
            subprocess.TimeoutExpired(cmd=["cmd"], timeout=5),
            None,
        ]
        mock_popen.return_value = mock_proc

        result = self.executor.run_streaming(
            ["cmd"], timeout=5,
        )

        assert result.success is False
        assert result.return_code == -1
        assert "partiel" in result.stdout
        mock_proc.kill.assert_called_once()

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_streaming_capture_stderr(self, mock_popen):
        """Test de la capture de stderr."""
        mock_popen.return_value = self._make_mock_proc(
            ["ok\n"], stderr="avertissement",
        )
        result = self.executor.run_streaming(["cmd"])

        assert result.stderr == "avertissement"

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_streaming_sans_logger(self, mock_popen):
        """Test du streaming sans logger."""
        mock_popen.return_value = self._make_mock_proc(
            ["ligne1\n"],
        )
        executor = LinuxCommandExecutor()
        result = executor.run_streaming(["cmd"])

        assert result.success is True
        assert result.stdout == "ligne1"


# --- Tests LinuxCommandExecutor dry_run ---


class TestLinuxCommandExecutorDryRun:
    """Tests pour le mode dry_run."""

    def setup_method(self):
        """Initialise l'exécuteur en mode dry_run."""
        self.mock_logger = MagicMock(spec=Logger)
        self.executor = LinuxCommandExecutor(
            logger=self.mock_logger,
            dry_run=True,
        )

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_dry_run_pas_execution(self, mock_run):
        """Test que subprocess n'est pas appelé."""
        self.executor.run(["rm", "-rf", "/"])
        mock_run.assert_not_called()

    def test_dry_run_log_commande(self):
        """Test que la commande est loguée avec [dry-run]."""
        self.executor.run(["echo", "test"])

        call_args = (
            self.mock_logger.log_info.call_args[0][0]
        )
        assert "[dry-run]" in call_args
        assert "echo test" in call_args

    def test_dry_run_retourne_succes(self):
        """Test que le résultat indique un succès."""
        result = self.executor.run(["echo", "test"])

        assert result.success is True
        assert result.return_code == 0
        assert result.duration == 0.0

    @patch(
        "linux_python_utils.commands.runner"
        ".subprocess.Popen"
    )
    def test_dry_run_streaming(self, mock_popen):
        """Test du dry_run avec run_streaming."""
        result = self.executor.run_streaming(
            ["echo", "test"]
        )

        assert result.success is True
        mock_popen.assert_not_called()


# --- Tests LinuxCommandExecutor environnement ---


class TestLinuxCommandExecutorEnv:
    """Tests pour la gestion de l'environnement."""

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    @patch.dict("os.environ", {"EXISTING": "val"})
    def test_default_env_fusionne(self, mock_run):
        """Test que default_env est fusionné."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="",
        )
        executor = LinuxCommandExecutor(
            default_env={"MY_VAR": "42"},
        )
        executor.run(["echo"])

        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert env["EXISTING"] == "val"
        assert env["MY_VAR"] == "42"

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    @patch.dict("os.environ", {"EXISTING": "val"})
    def test_env_appel_prioritaire(self, mock_run):
        """Test que l'env de l'appel est prioritaire."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="",
        )
        executor = LinuxCommandExecutor(
            default_env={"KEY": "default"},
        )
        executor.run(["echo"], env={"KEY": "override"})

        call_kwargs = mock_run.call_args[1]
        env = call_kwargs["env"]
        assert env["KEY"] == "override"

    @patch(
        "linux_python_utils.commands.runner.subprocess.run"
    )
    def test_aucun_env_passe_none(self, mock_run):
        """Test que sans env, subprocess reçoit None."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr="",
        )
        executor = LinuxCommandExecutor()
        executor.run(["echo"])

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] is None
