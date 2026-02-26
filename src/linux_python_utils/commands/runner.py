"""Exécuteur de commandes Linux via subprocess.

Ce module fournit LinuxCommandExecutor, une implémentation concrète
de CommandExecutor qui utilise subprocess pour exécuter des commandes
sur un système Linux.

Les commandes exécutées par root sont distinguées visuellement des
commandes utilisateur :
    - Dans les logs fichier : préfixe textuel [ROOT] ou [user]
    - En console (optionnel) : codes ANSI couleur + gras via
      AnsiCommandFormatter

Example :
    Exécution simple avec logs fichier uniquement :

        from linux_python_utils.commands import LinuxCommandExecutor

        executor = LinuxCommandExecutor(logger=logger)
        result = executor.run(["ls", "-la"])
        print(result.stdout)
        print(result.executed_as_root)  # True si lancé en root

    Exécution avec affichage console coloré en plus des logs :

        from linux_python_utils import FileLogger
        from linux_python_utils.commands import (
            LinuxCommandExecutor,
            AnsiCommandFormatter,
        )

        logger = FileLogger("/var/log/app.log")
        executor = LinuxCommandExecutor(
            logger=logger,
            console_formatter=AnsiCommandFormatter(),
        )
        result = executor.run_streaming(
            ["rsync", "-av", "/src", "/dst"]
        )
"""

import os
import subprocess  # nosec B404
import time
from typing import Dict, List, Optional

from linux_python_utils.commands.base import (
    CommandExecutor,
    CommandResult,
)
from linux_python_utils.commands.formatter import (
    CommandFormatter,
    PlainCommandFormatter,
)
from linux_python_utils.logging.base import Logger


class LinuxCommandExecutor(CommandExecutor):
    """Exécuteur de commandes Linux via subprocess.

    Supporte l'exécution avec capture de sortie et le streaming
    en temps réel vers un logger. Le mode dry_run permet de
    simuler l'exécution sans lancer de processus.

    Les messages de log utilisent PlainCommandFormatter avec les
    préfixes [ROOT] ou [user] selon les privilèges détectés à
    l'initialisation via os.getuid().

    Un console_formatter optionnel (ex: AnsiCommandFormatter)
    permet d'afficher en parallèle des messages colorés sur stdout,
    indépendamment du logger fichier.

    Attributes:
        _logger: Logger optionnel pour les logs fichier.
        _default_env: Variables d'environnement par défaut.
        _default_timeout: Timeout par défaut en secondes.
        _dry_run: Mode simulation.
        _is_root: True si le processus courant est root (uid 0).
        _plain: Formateur texte brut pour les logs fichier.
        _console_formatter: Formateur optionnel pour la console.
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        default_env: Optional[Dict[str, str]] = None,
        default_timeout: Optional[int] = None,
        dry_run: bool = False,
        console_formatter: Optional[CommandFormatter] = None,
    ) -> None:
        """Initialise l'exécuteur de commandes.

        Détecte automatiquement si le processus courant s'exécute
        en root via os.getuid() == 0.

        Args:
            logger: Logger optionnel pour les sorties fichier.
            default_env: Variables d'environnement par défaut
                (fusionnées avec os.environ).
            default_timeout: Timeout par défaut en secondes.
            dry_run: Si True, simule sans exécuter.
            console_formatter: Formateur optionnel pour la console
                (ex: AnsiCommandFormatter()). Indépendant du logger :
                utiliser FileLogger sans console_output=True pour
                éviter la duplication de sortie console.
        """
        self._logger = logger
        self._default_env = default_env
        self._default_timeout = default_timeout
        self._dry_run = dry_run
        self._is_root: bool = os.getuid() == 0
        self._plain = PlainCommandFormatter()
        self._console_formatter = console_formatter

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

    def _log(self, message: str) -> None:
        """Envoie un message au logger fichier si disponible.

        Args:
            message: Message à logger.
        """
        if self._logger:
            self._logger.log_info(message)

    def _log_error(self, message: str) -> None:
        """Envoie un message d'erreur au logger si disponible.

        Args:
            message: Message d'erreur à logger.
        """
        if self._logger:
            self._logger.log_error(message)

    def _console(self, message: str) -> None:
        """Affiche un message sur la console via le formatter.

        N'affiche rien si aucun console_formatter n'est configuré.

        Args:
            message: Message à afficher sur la console.
        """
        if self._console_formatter:
            print(message)

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
        plain_msg = self._plain.format_dry_run(
            command, self._is_root
        )
        self._log(plain_msg)

        if self._console_formatter:
            self._console(
                self._console_formatter.format_dry_run(
                    command, self._is_root
                )
            )

        return CommandResult(
            command=command,
            return_code=0,
            stdout="",
            stderr="",
            success=True,
            duration=0.0,
            executed_as_root=self._is_root,
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
        Préfixe les messages de log avec [ROOT] ou [user] selon
        les privilèges détectés à l'initialisation.

        Args:
            command: Commande sous forme de liste.
            env: Variables d'environnement supplémentaires.
            cwd: Répertoire de travail.
            timeout: Timeout en secondes (prioritaire).

        Returns:
            CommandResult avec les sorties capturées et
            executed_as_root indiquant le contexte d'exécution.

        Note:
            Logue une erreur si le code retour est non-nul et qu'un
            logger est configuré.
        """
        if self._dry_run:
            return self._make_dry_run_result(command)

        effective_env = self._build_env(env)
        effective_timeout = self._resolve_timeout(timeout)

        plain_msg = self._plain.format_start(
            command, self._is_root
        )
        self._log(plain_msg)

        if self._console_formatter:
            self._console(
                self._console_formatter.format_start(
                    command, self._is_root
                )
            )

        start = time.monotonic()
        try:
            proc = subprocess.run(  # nosec B603
                command,
                capture_output=True,
                text=True,
                env=effective_env,
                cwd=cwd,
                timeout=effective_timeout,
            )
            duration = time.monotonic() - start
            if proc.returncode != 0:
                self._log_error(
                    f"Code retour {proc.returncode} : "
                    f"{' '.join(command)}"
                )
            return CommandResult(
                command=command,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                success=proc.returncode == 0,
                duration=duration,
                executed_as_root=self._is_root,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.monotonic() - start
            self._log_error(
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
                executed_as_root=self._is_root,
            )
        except OSError as e:
            duration = time.monotonic() - start
            self._log_error(f"Erreur système : {e}")
            return CommandResult(
                command=command,
                return_code=-1,
                stdout="",
                stderr=str(e),
                success=False,
                duration=duration,
                executed_as_root=self._is_root,
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
            CommandResult avec les sorties capturées et
            executed_as_root indiquant le contexte d'exécution.

        Note:
            Logue une erreur si le code retour est non-nul et qu'un
            logger est configuré.
        """
        if self._dry_run:
            return self._make_dry_run_result(command)

        effective_env = self._build_env(env)
        effective_timeout = self._resolve_timeout(timeout)

        plain_msg = self._plain.format_start_streaming(
            command, self._is_root
        )
        self._log(plain_msg)

        if self._console_formatter:
            self._console(
                self._console_formatter.format_start_streaming(
                    command, self._is_root
                )
            )

        start = time.monotonic()
        stdout_lines: List[str] = []
        try:
            with subprocess.Popen(  # nosec B603
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
                    self._log(
                        self._plain.format_line(
                            stripped, self._is_root
                        )
                    )
                    if self._console_formatter:
                        self._console(
                            self._console_formatter.format_line(
                                stripped, self._is_root
                            )
                        )

                proc.wait(timeout=effective_timeout)
                stderr = proc.stderr.read()

                duration = time.monotonic() - start
                if proc.returncode != 0:
                    self._log_error(
                        f"Code retour {proc.returncode} : "
                        f"{' '.join(command)}"
                    )
                return CommandResult(
                    command=command,
                    return_code=proc.returncode,
                    stdout="\n".join(stdout_lines),
                    stderr=stderr,
                    success=proc.returncode == 0,
                    duration=duration,
                    executed_as_root=self._is_root,
                )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            duration = time.monotonic() - start
            stderr = ""
            if proc.stderr:
                stderr = proc.stderr.read()
            self._log_error(
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
                executed_as_root=self._is_root,
            )
        except OSError as e:
            duration = time.monotonic() - start
            self._log_error(f"Erreur système : {e}")
            return CommandResult(
                command=command,
                return_code=-1,
                stdout="\n".join(stdout_lines),
                stderr=str(e),
                success=False,
                duration=duration,
                executed_as_root=self._is_root,
            )
