"""Implémentation concrète du logger avec fichier."""

# stdlib
import logging
import os
from typing import Any, Dict, Optional

# local
from linux_python_utils.logging.ansi_colors import AnsiColors
from linux_python_utils.logging.base import Logger

_NIVEAUX = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _open_secure(path: str) -> int:
    """Ouvre le log avec O_NOFOLLOW/0o600 (anti-symlink, anti-lecture)."""
    flags = os.O_CREAT | os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
    return os.open(path, flags, 0o600)


_LEVEL_COLORS = {
    logging.INFO: AnsiColors.BLUE,
    logging.WARNING: AnsiColors.ORANGE,
    logging.ERROR: AnsiColors.RED,
    logging.CRITICAL: AnsiColors.RED,
}


class _ColoredFormatter(logging.Formatter):
    """Formateur qui préfixe chaque message d'un code ANSI selon le niveau."""

    def format(self, record: logging.LogRecord) -> str:
        """Formate le message avec la couleur du niveau de log.

        Args:
            record: Enregistrement de log à formater.

        Returns:
            Message formaté entouré des codes ANSI correspondants.
        """
        color = _LEVEL_COLORS.get(record.levelno, AnsiColors.RESET)
        return f"{color}{super().format(record)}{AnsiColors.RESET}"


class FileLogger(Logger):
    """
    Logger qui écrit dans un fichier avec option console.

    Caractéristiques:
    - Logger unique par instance (évite les conflits)
    - Encodage UTF-8 explicite
    - Flush immédiat après chaque log
    - Pas de propagation (évite les logs en double)
    - Support optionnel de la sortie console colorée
    """

    def __init__(
        self,
        log_file: str,
        config: Optional[Dict[str, Any]] = None,
        console_output: bool = False,
        colored_console: bool = False,
    ) -> None:
        """Initialise le logger.

        Args:
            log_file: Chemin du fichier de log.
            config: Configuration optionnelle (dict ou ConfigurationManager).
                Clés supportées: logging.level, logging.format.
            console_output: Activer la sortie console en plus du fichier.
            colored_console: Coloriser la sortie console par niveau de log.
                Sans effet si console_output est False.
                Le fichier log reste toujours en plain-text.
        """
        self.log_file = log_file

        # Créer le répertoire de logs si nécessaire
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Configuration depuis dict ou ConfigurationManager
        if config is not None:
            if hasattr(config, 'get') and callable(config.get):
                # ConfigurationManager avec accès par chemin pointé
                try:
                    log_level_str = config.get("logging.level", "INFO")
                    log_format = config.get(
                        "logging.format",
                        "%(asctime)s - %(levelname)s - %(message)s"
                    )
                except TypeError:
                    # Dict standard
                    logging_cfg = config.get("logging", {})
                    log_level_str = logging_cfg.get("level", "INFO")
                    log_format = logging_cfg.get(
                        "format",
                        "%(asctime)s - %(levelname)s - %(message)s"
                    )
            else:
                log_level_str = "INFO"
                log_format = "%(asctime)s - %(levelname)s - %(message)s"
        else:
            log_level_str = "INFO"
            log_format = "%(asctime)s - %(levelname)s - %(message)s"

        niveau = log_level_str.upper()
        if niveau not in _NIVEAUX:
            raise ValueError(f"Niveau de log invalide : {log_level_str!r}")
        log_level = getattr(logging, niveau)

        # Créer un logger unique par instance
        self.logger = logging.getLogger(log_file)
        self.logger.setLevel(log_level)

        # Éviter les handlers dupliqués
        if not self.logger.handlers:
            # Handler fichier — fd sécurisé (O_NOFOLLOW, 0o600)
            fd = _open_secure(log_file)
            file_handler = logging.StreamHandler(
                os.fdopen(fd, "a", encoding="utf-8")
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(file_handler)
            self.handler = file_handler

            # Handler console optionnel
            if console_output:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(log_level)
                fmt = (
                    _ColoredFormatter(log_format)
                    if colored_console
                    else logging.Formatter(log_format)
                )
                console_handler.setFormatter(fmt)
                self.logger.addHandler(console_handler)
        else:
            self.handler = self.logger.handlers[0]

        # Ne pas propager pour éviter les logs en double
        self.logger.propagate = False

    def _flush(self) -> None:
        """Force l'écriture immédiate sur le disque."""
        if hasattr(self, 'handler') and self.handler:
            self.handler.flush()

    def log_info(self, message: str) -> None:
        """Log un message d'information."""
        self.logger.info(message)
        self._flush()

    def log_warning(self, message: str) -> None:
        """Log un avertissement."""
        self.logger.warning(message)
        self._flush()

    def log_error(self, message: str) -> None:
        """Log une erreur."""
        self.logger.error(message)
        self._flush()

    def log_to_file(self, message: str) -> None:
        """Écrit directement dans le fichier (sans passer par logging).

        Utile pour les logs bruts sans formatage.
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fd = _open_secure(self.log_file)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {message}\n")
