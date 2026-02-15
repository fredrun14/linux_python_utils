"""Exécuteur de commandes Linux via subprocess.

Ce module fournit LinuxCommandExecutor, une implémentation concrète
de CommandExecutor qui utilise subprocess pour exécuter des commandes
sur un système Linux.

Example:
    Exécution simple :

        from linux_python_utils.commands import (
            LinuxCommandExecutor,
        )

        executor = LinuxCommandExecutor()
        result = executor.run(["ls", "-la"])
        print(result.stdout)

    Exécution avec streaming vers un logger :

        from linux_python_utils import FileLogger
        from linux_python_utils.commands import (
            LinuxCommandExecutor,
        )

        logger = FileLogger("/var/log/app.log")
        executor = LinuxCommandExecutor(logger=logger)
        result = executor.run_streaming(
            ["rsync", "-av", "/src", "/dst"]
        )
"""

import os
import subprocess
import time
from typing import Dict, List, Optional

from linux_python_utils.commands.base import (
    CommandExecutor,
    CommandResult,
)
from linux_python_utils.logging.base import Logger


class LinuxCommandExecutor(CommandExecutor):
    """Exécuteur de commandes Linux via subprocess.

    Supporte l'exécution avec capture de sortie et le streaming
    en temps réel vers un logger. Le mode dry_run permet de
    simuler l'exécution sans lancer de processus.

    Attributes:
        _logger: Logger optionnel.
        _default_env: Variables d'environnement par défaut.
        _default_timeout: Timeout par défaut en secondes.
        _dry_run: Mode simulation.
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        default_env: Optional[Dict[str, str]] = None,
        default_timeout: Optional[int] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialise l'exécuteur de commandes.

        Args:
            logger: Logger optionnel pour les sorties.
            default_env: Variables d'environnement par défaut
                (fusionnées avec os.environ).
            default_timeout: Timeout par défaut en secondes.
            dry_run: Si True, simule sans exécuter.
        """
        self._logger = logger
        self._default_env = default_env
        self._default_timeout = default_timeout
        self._dry_run = dry_run

    def _build_env(
        self,
        env: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, str]]:
        """Construit l'environnement d'exécution.

        Fusionne os.environ, default_env et env spécifique.
        Retourne None si aucun environnement personnalisé
        (subprocess utilisera os.environ par défaut).

        Args:
            env: Variables d'environnement spécifiques.

        Returns:
            Dictionnaire d'environnement ou None.
        """
        if self._default_env is None and env is None:
            return None
        merged = os.environ.copy()
        if self._default_env:
            merged.update(self._default_env)
        if env:
            merged.update(env)
        return merged

    def _resolve_timeout(
        self,
        timeout: Optional[int] = None,
    ) -> Optional[int]:
        """Détermine le timeout effectif.

        Le timeout spécifique à l'appel est prioritaire
        sur le timeout par défaut.

        Args:
            timeout: Timeout spécifique à cet appel.

        Returns:
            Timeout en secondes ou None (pas de limite).
        """
        if timeout is not None:
            return timeout
        return self._default_timeout

    def _make_dry_run_result(
        self,
        command: List[str],
    ) -> CommandResult:
        """Crée un CommandResult pour le mode dry_run.

        Args:
            command: Commande simulée.

        Returns:
            CommandResult avec code retour 0.
        """
        cmd_str = " ".join(command)
        if self._logger:
            self._logger.log_info(
                f"[dry-run] {cmd_str}"
            )
        return CommandResult(
            command=command,
            return_code=0,
            stdout="",
            stderr="",
            success=True,
            duration=0.0,
        )

    def run(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """Exécute une commande et retourne le résultat.

        Utilise subprocess.run pour capturer stdout et stderr.

        Args:
            command: Commande sous forme de liste.
            env: Variables d'environnement supplémentaires.
            cwd: Répertoire de travail.
            timeout: Timeout en secondes (prioritaire).

        Returns:
            CommandResult avec les sorties capturées.
        """
        if self._dry_run:
            return self._make_dry_run_result(command)

        effective_env = self._build_env(env)
        effective_timeout = self._resolve_timeout(timeout)

        if self._logger:
            self._logger.log_info(
                f"Exécution : {' '.join(command)}"
            )

        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=effective_env,
                cwd=cwd,
                timeout=effective_timeout,
            )
            duration = time.monotonic() - start
            return CommandResult(
                command=command,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                success=proc.returncode == 0,
                duration=duration,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.monotonic() - start
            if self._logger:
                self._logger.log_error(
                    f"Timeout après {effective_timeout}s : "
                    f"{' '.join(command)}"
                )
            return CommandResult(
                command=command,
                return_code=-1,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                success=False,
                duration=duration,
            )
        except OSError as e:
            duration = time.monotonic() - start
            if self._logger:
                self._logger.log_error(
                    f"Erreur système : {e}"
                )
            return CommandResult(
                command=command,
                return_code=-1,
                stdout="",
                stderr=str(e),
                success=False,
                duration=duration,
            )

    def run_streaming(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """Exécute avec sortie en temps réel vers le logger.

        Utilise subprocess.Popen pour lire stdout ligne par
        ligne et l'envoyer au logger en temps réel. Stderr
        est capturé séparément.

        Args:
            command: Commande sous forme de liste.
            env: Variables d'environnement supplémentaires.
            cwd: Répertoire de travail.
            timeout: Timeout en secondes (prioritaire).

        Returns:
            CommandResult avec les sorties capturées.
        """
        if self._dry_run:
            return self._make_dry_run_result(command)

        effective_env = self._build_env(env)
        effective_timeout = self._resolve_timeout(timeout)

        if self._logger:
            self._logger.log_info(
                f"Exécution (streaming) : "
                f"{' '.join(command)}"
            )

        start = time.monotonic()
        stdout_lines: List[str] = []
        try:
            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=effective_env,
                cwd=cwd,
            ) as proc:
                for line in proc.stdout:
                    stripped = line.rstrip("\n")
                    stdout_lines.append(stripped)
                    if self._logger:
                        self._logger.log_info(stripped)

                proc.wait(timeout=effective_timeout)
                stderr = proc.stderr.read()

                duration = time.monotonic() - start
                return CommandResult(
                    command=command,
                    return_code=proc.returncode,
                    stdout="\n".join(stdout_lines),
                    stderr=stderr,
                    success=proc.returncode == 0,
                    duration=duration,
                )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            duration = time.monotonic() - start
            stderr = ""
            if proc.stderr:
                stderr = proc.stderr.read()
            if self._logger:
                self._logger.log_error(
                    f"Timeout après {effective_timeout}s : "
                    f"{' '.join(command)}"
                )
            return CommandResult(
                command=command,
                return_code=-1,
                stdout="\n".join(stdout_lines),
                stderr=stderr,
                success=False,
                duration=duration,
            )
        except OSError as e:
            duration = time.monotonic() - start
            if self._logger:
                self._logger.log_error(
                    f"Erreur système : {e}"
                )
            return CommandResult(
                command=command,
                return_code=-1,
                stdout="\n".join(stdout_lines),
                stderr=str(e),
                success=False,
                duration=duration,
            )
