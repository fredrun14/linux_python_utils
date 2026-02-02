"""Installation de scripts bash sur le système de fichiers.

Ce module fournit des classes pour installer des scripts bash
générés à partir de BashScriptConfig.

Example:
    Installation d'un script:

        from linux_python_utils import BashScriptInstaller, BashScriptConfig

        installer = BashScriptInstaller(logger, file_manager)
        config = BashScriptConfig(exec_command="echo 'Hello'")
        installer.install("/usr/local/bin/hello.sh", config)
"""

import os
from abc import ABC, abstractmethod

from linux_python_utils.logging import Logger
from linux_python_utils.filesystem import FileManager
from linux_python_utils.scripts.config import BashScriptConfig


class ScriptInstaller(ABC):
    """Interface abstraite pour l'installation de scripts.

    Cette classe définit le contrat pour toute implémentation
    d'installateur de scripts.
    """

    @abstractmethod
    def install(self, path: str, config: BashScriptConfig) -> bool:
        """Installe un script à partir de sa configuration.

        Args:
            path: Chemin où installer le script.
            config: Configuration du script à générer.

        Returns:
            True si l'installation a réussi, False sinon.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Vérifie si un script existe déjà.

        Args:
            path: Chemin du script à vérifier.

        Returns:
            True si le script existe, False sinon.
        """
        pass


class BashScriptInstaller(ScriptInstaller):
    """Installateur de scripts bash pour systèmes Linux.

    Cette classe gère la création de scripts bash sur le système
    de fichiers, incluant la génération du contenu et les
    permissions d'exécution.

    Attributes:
        logger: Instance de Logger pour la journalisation.
        file_manager: Gestionnaire de fichiers pour les opérations I/O.
        default_mode: Permissions par défaut (0o755).

    Example:
        >>> installer = BashScriptInstaller(logger, file_manager)
        >>> config = BashScriptConfig(exec_command="ls -la")
        >>> installer.install("/tmp/test.sh", config)
        True
    """

    def __init__(
        self,
        logger: Logger,
        file_manager: FileManager,
        default_mode: int = 0o755
    ) -> None:
        """Initialise l'installateur avec ses dépendances.

        Args:
            logger: Instance de Logger pour la journalisation.
            file_manager: Gestionnaire de fichiers.
            default_mode: Permissions par défaut pour les scripts.
        """
        self._logger: Logger = logger
        self._file_manager: FileManager = file_manager
        self._default_mode: int = default_mode

    def install(self, path: str, config: BashScriptConfig) -> bool:
        """Installe un script bash à partir de sa configuration.

        Génère le contenu du script via BashScriptConfig.to_bash_script(),
        crée le fichier et le rend exécutable.

        Args:
            path: Chemin où installer le script.
            config: Configuration du script à générer.

        Returns:
            True si l'installation a réussi, False sinon.
        """
        if self.exists(path):
            self._logger.log_info(
                f"Le script {path} existe déjà. "
                "Aucune modification apportée."
            )
            return True

        script_content: str = config.to_bash_script()

        if not self._file_manager.create_file(path, script_content):
            self._logger.log_error(f"Impossible de créer le script {path}")
            return False

        if not self._set_executable(path):
            return False

        self._logger.log_info(f"Script {path} installé avec succès.")
        return True

    def exists(self, path: str) -> bool:
        """Vérifie si un script existe déjà.

        Args:
            path: Chemin du script à vérifier.

        Returns:
            True si le script existe, False sinon.
        """
        return self._file_manager.file_exists(path)

    def _set_executable(self, path: str) -> bool:
        """Rend le script exécutable.

        Args:
            path: Chemin du script.

        Returns:
            True si l'opération a réussi, False sinon.
        """
        try:
            os.chmod(path, self._default_mode)
            return True
        except OSError as e:
            self._logger.log_error(
                f"Impossible de rendre le script exécutable : {e}"
            )
            return False
