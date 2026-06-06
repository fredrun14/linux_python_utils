"""Gestion idempotente des utilisateurs Unix."""

import grp
import pwd
from typing import Optional

from linux_python_utils.commands import CommandBuilder, LinuxCommandExecutor
from linux_python_utils.commands.base import CommandExecutor
from linux_python_utils.errors import CommandExecutionError
from linux_python_utils.identity.base import UserManagerBase, _valider_nom
from linux_python_utils.logging import Logger


class LinuxUserManager(UserManagerBase):
    """Crée ou corrige les utilisateurs Unix via useradd / usermod."""

    def __init__(
        self,
        logger: Optional[Logger] = None,
        executor: Optional[CommandExecutor] = None,
    ) -> None:
        """Initialise le gestionnaire avec ses dépendances.

        Args:
            logger: Logger optionnel pour les messages d'information.
            executor: Exécuteur de commandes optionnel ; construit par
                défaut si absent.
        """
        self._logger = logger
        self._executor = executor or LinuxCommandExecutor(logger=logger)
        self._prefix = "[LinuxUserManager]"

    def ensure_user(
        self,
        name: str,
        uid: int,
        shell: str,
        comment: str,
        create_home: bool,
    ) -> None:
        """Crée ou corrige l'utilisateur Unix avec l'UID donné.

        Args:
            name: Nom d'utilisateur (convention Unix : minuscules,
                chiffres, tiret, underscore ; pas de tiret initial).
            uid: UID souhaité.
            shell: Shell de connexion.
            comment: Commentaire GECOS.
            create_home: Créer le répertoire home si absent.

        Raises:
            ValueError: Si ``name`` ne respecte pas la convention Unix.
            CommandExecutionError: Si usermod/useradd retourne un code
                non nul.
        """
        _valider_nom(name)
        try:
            existing = pwd.getpwnam(name)
            if existing.pw_uid != uid:
                self._logger.log_info(
                    f"{self._prefix} Utilisateur '{name}' "
                    f"a l'UID {existing.pw_uid} "
                    f"(attendu {uid}) — correction"
                )
                cmd = (
                    CommandBuilder("usermod")
                    .with_options(["--uid", str(uid)])
                    .with_args([name])
                    .build()
                )
                result = self._executor.run(cmd)
                if not result.success:
                    raise CommandExecutionError(
                        f"{self._prefix} usermod '{name}' "
                        f"a échoué (code {result.return_code})"
                    )
            else:
                self._logger.log_info(
                    f"{self._prefix} Utilisateur '{name}' "
                    f"(UID {uid}) déjà présent — skip"
                )
        except KeyError:
            self._logger.log_info(
                f"{self._prefix} Création de l'utilisateur"
                f" '{name}' (UID {uid})"
            )
            builder = (
                CommandBuilder("useradd")
                .with_options(["--uid", str(uid)])
                .with_options(["--shell", shell])
                .with_options(["--comment", comment])
            )
            if create_home:
                builder = builder.with_flag("--create-home")
            result = self._executor.run(builder.with_args([name]).build())
            if not result.success:
                raise CommandExecutionError(
                    f"{self._prefix} useradd '{name}' "
                    f"a échoué (code {result.return_code})"
                )

    def ensure_user_groups(
        self,
        username: str,
        groups: list[str],
    ) -> None:
        """Ajoute l'utilisateur aux groupes manquants en une seule commande.

        Comportement best-effort : un groupe inexistant sur le système
        est loggé (warning) puis ignoré. La méthode réussit même si aucun
        groupe n'a pu être appliqué (tous absents ou utilisateur déjà membre).

        Args:
            username: Nom d'utilisateur (convention Unix).
            groups: Liste des groupes secondaires souhaités.

        Raises:
            ValueError: Si ``username`` ou un nom de groupe ne respecte
                pas la convention Unix.
            CommandExecutionError: Si usermod retourne un code non nul.
        """
        _valider_nom(username)
        for group_name in groups:
            _valider_nom(group_name)
        missing: list[str] = []
        for group_name in groups:
            try:
                group = grp.getgrnam(group_name)
            except KeyError:
                self._logger.log_warning(
                    f"{self._prefix} Groupe '{group_name}' "
                    f"introuvable pour '{username}' — skip"
                )
                continue
            if username not in group.gr_mem:
                missing.append(group_name)

        if not missing:
            self._logger.log_info(
                f"{self._prefix} Utilisateur '{username}' "
                f"déjà membre de tous les groupes — skip"
            )
            return

        groups_str = ",".join(missing)
        self._logger.log_info(
            f"{self._prefix} Ajout de '{username}' aux groupes : {groups_str}"
        )
        cmd = (
            CommandBuilder("usermod")
            .with_flag("--append")
            .with_options(["--groups", groups_str])
            .with_args([username])
            .build()
        )
        result = self._executor.run(cmd)
        if not result.success:
            raise CommandExecutionError(
                f"{self._prefix} usermod --append '{username}' "
                f"a échoué (code {result.return_code})"
            )
