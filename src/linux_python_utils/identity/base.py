"""Interfaces abstraites pour la gestion idempotente des identités Unix."""

from abc import ABC, abstractmethod


class GroupManagerBase(ABC):
    """Interface abstraite pour la gestion idempotente des groupes Unix."""

    @abstractmethod
    def ensure_group(self, name: str, gid: int) -> None:
        """Crée ou corrige le groupe Unix avec le GID donné.

        Args:
            name: Nom du groupe.
            gid: GID souhaité.
        """


class UserManagerBase(ABC):
    """Interface abstraite pour la gestion idempotente des utilisateurs Unix."""

    @abstractmethod
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
            name: Nom d'utilisateur.
            uid: UID souhaité.
            shell: Shell de connexion.
            comment: Commentaire GECOS.
            create_home: Créer le répertoire home si absent.
        """

    @abstractmethod
    def ensure_user_groups(
        self,
        username: str,
        groups: list[str],
    ) -> None:
        """Ajoute l'utilisateur aux groupes manquants en une seule commande.

        Args:
            username: Nom d'utilisateur.
            groups: Liste des groupes secondaires souhaités.
        """
