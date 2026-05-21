"""Gestion du répertoire de configuration XDG pour une application."""

# stdlib
from pathlib import Path

# third-party
from platformdirs import user_config_path


class XdgAppConfig:
    """Gestion du répertoire de configuration XDG pour une application.

    Encapsule la convention XDG Base Directory Specification :
    le répertoire de configuration utilisateur par défaut est
    ``~/.config/<app_name>/`` sur Linux.

    Attributes:
        _app_name: Nom de l'application (slug kebab-case).

    Example:
        >>> cfg = XdgAppConfig("fedora-post-install")
        >>> cfg.config_dir
        PosixPath('/home/user/.config/fedora-post-install')
        >>> cfg.init_config_file("[log]\\nlevel = 'INFO'\\n")
        PosixPath('/home/user/.config/fedora-post-install/global.toml')
    """

    def __init__(self, app_name: str) -> None:
        """Initialise la configuration XDG pour l'application.

        Args:
            app_name: Nom de l'application en kebab-case
                (ex: 'fedora-post-install', 'backup-py-manager').
        """
        self._app_name = app_name

    @property
    def config_dir(self) -> Path:
        """Retourne le répertoire de configuration XDG de l'application.

        Returns:
            Chemin vers ~/.config/<app_name>/ (non créé).
        """
        return user_config_path(self._app_name)

    def ensure_subdir(self, name: str) -> Path:
        """Crée un sous-répertoire dans le répertoire de config.

        Args:
            name: Nom du sous-répertoire (ex: 'configs', 'logs').

        Returns:
            Chemin absolu du sous-répertoire créé.
        """
        subdir = self.config_dir / name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def init_config_file(
        self,
        template: str,
        filename: str = "global.toml",
        force: bool = False,
    ) -> Path:
        """Crée le fichier de configuration avec le template fourni.

        Crée le répertoire ~/.config/<app>/ si nécessaire, puis écrit
        le template dans filename. Lève FileExistsError si le fichier
        existe déjà et que force est False.

        Args:
            template: Contenu à écrire dans le fichier de configuration.
            filename: Nom du fichier de configuration.
                Défaut: 'global.toml'.
            force: Si True, écrase le fichier existant sans erreur.

        Returns:
            Chemin absolu du fichier créé.

        Raises:
            FileExistsError: Si le fichier existe et force est False.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / filename
        if config_file.exists() and not force:
            raise FileExistsError(
                f"Le fichier de configuration existe déjà : "
                f"{config_file}. "
                f"Utilisez force=True pour l'écraser."
            )
        config_file.write_text(template, encoding="utf-8")
        return config_file
