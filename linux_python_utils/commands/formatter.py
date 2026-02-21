"""Formateurs pour l'affichage des messages de commandes système.

Ce module fournit une hiérarchie de formateurs permettant d'afficher
les messages de commandes différemment selon le contexte (fichier de
log ou console) et les privilèges d'exécution (root ou utilisateur).

Classes :
    CommandFormatter : Interface abstraite de formatage.
    PlainCommandFormatter : Texte brut avec préfixes [ROOT]/[user].
    AnsiCommandFormatter : Codes ANSI colorés pour la console.

Example :
    Utilisation typique avec LinuxCommandExecutor :

        from linux_python_utils.commands import (
            LinuxCommandExecutor,
            AnsiCommandFormatter,
        )

        executor = LinuxCommandExecutor(
            logger=logger,
            console_formatter=AnsiCommandFormatter(),
        )
        result = executor.run(["rsync", "-av", "/src", "/dst"])

Note :
    AnsiCommandFormatter vérifie automatiquement si la sortie est
    un terminal (TTY) avant d'émettre des codes ANSI, évitant
    ainsi de polluer les pipes ou les redirections.
"""

import sys
from abc import ABC, abstractmethod
from typing import List


class CommandFormatter(ABC):
    """Interface abstraite pour formater les messages de commande.

    Chaque implémentation définit sa propre représentation visuelle
    des messages d'exécution, de streaming et de simulation.

    Les formateurs reçoivent le contexte d'exécution (is_root)
    pour adapter leur affichage en conséquence.
    """

    @abstractmethod
    def format_start(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le message de début d'exécution.

        Args:
            command: Commande sous forme de liste.
            is_root: True si la commande est exécutée en root.

        Returns:
            Message formaté prêt à l'affichage.
        """
        pass

    @abstractmethod
    def format_start_streaming(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le message de début d'exécution en streaming.

        Args:
            command: Commande sous forme de liste.
            is_root: True si la commande est exécutée en root.

        Returns:
            Message formaté prêt à l'affichage.
        """
        pass

    @abstractmethod
    def format_dry_run(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le message de simulation (mode dry-run).

        Args:
            command: Commande sous forme de liste.
            is_root: True si la commande est exécutée en root.

        Returns:
            Message formaté prêt à l'affichage.
        """
        pass

    @abstractmethod
    def format_line(
        self, line: str, is_root: bool
    ) -> str:
        """Formate une ligne de sortie en mode streaming.

        Args:
            line: Ligne de sortie de la commande.
            is_root: True si la commande est exécutée en root.

        Returns:
            Ligne formatée prête à l'affichage.
        """
        pass


class PlainCommandFormatter(CommandFormatter):
    """Formateur texte brut pour les logs fichier.

    Produit des messages avec préfixe textuel [ROOT] ou [user].
    N'utilise aucun code ANSI : compatible avec les fichiers de log,
    les outils grep et les éditeurs de texte.

    Example :
        Sortie pour une commande root :
            [ROOT] Exécution : rsync -av /src /dst

        Sortie pour un utilisateur standard :
            [user] Exécution : rsync -av /src /dst
    """

    _ROOT_PREFIX = "[ROOT]"
    _USER_PREFIX = "[user]"

    def _prefix(self, is_root: bool) -> str:
        """Retourne le préfixe textuel selon le contexte.

        Args:
            is_root: True si l'exécution est en root.

        Returns:
            Préfixe [ROOT] ou [user].
        """
        return self._ROOT_PREFIX if is_root else self._USER_PREFIX

    def format_start(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le début d'exécution avec préfixe textuel."""
        cmd_str = " ".join(command)
        return f"{self._prefix(is_root)} Exécution : {cmd_str}"

    def format_start_streaming(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le début d'exécution streaming avec préfixe."""
        cmd_str = " ".join(command)
        return (
            f"{self._prefix(is_root)} "
            f"Exécution (streaming) : {cmd_str}"
        )

    def format_dry_run(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le message de simulation avec préfixe."""
        cmd_str = " ".join(command)
        return f"{self._prefix(is_root)} [dry-run] {cmd_str}"

    def format_line(
        self, line: str, is_root: bool
    ) -> str:
        """Retourne la ligne sans modification."""
        return line


class AnsiCommandFormatter(CommandFormatter):
    """Formateur ANSI coloré pour la sortie console.

    Distingue visuellement les exécutions root (jaune-or gras)
    des exécutions utilisateur standard (vert). Les lignes de
    contenu streaming ne sont pas stylisées pour conserver la
    lisibilité de la sortie de la commande.

    N'émet aucun code ANSI si stdout n'est pas un terminal TTY,
    évitant ainsi de polluer les pipes ou les redirections.

    Styles ANSI :
        ROOT    → \\033[1;33m (jaune-or gras) — distinct des erreurs rouges
        user    → \\033[0;32m (vert normal)
        dry-run → \\033[0;90m (gris discret)
        reset   → \\033[0m

    Example :
        Sortie console pour une commande root :
            [ROOT] Exécution : rsync -av /src /dst  (en jaune gras)

        Sortie console pour un utilisateur standard :
            [user] Exécution : rsync -av /src /dst  (en vert)
    """

    RESET = "\033[0m"
    ROOT_STYLE = "\033[1;33m"   # Jaune-or gras
    USER_STYLE = "\033[0;32m"   # Vert normal
    DRY_STYLE = "\033[0;90m"    # Gris discret

    ROOT_PREFIX = "[ROOT]"
    USER_PREFIX = "[user]"

    def _is_tty(self) -> bool:
        """Vérifie si stdout est un terminal interactif (TTY).

        Returns:
            True si stdout est un TTY, False sinon.
        """
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def _prefix(self, is_root: bool) -> str:
        """Retourne le préfixe selon le contexte.

        Args:
            is_root: True si l'exécution est en root.

        Returns:
            Préfixe [ROOT] ou [user].
        """
        return self.ROOT_PREFIX if is_root else self.USER_PREFIX

    def _apply_style(self, text: str, is_root: bool) -> str:
        """Applique le style ANSI si on est dans un TTY.

        Args:
            text: Texte à styliser.
            is_root: True pour le style root, False pour user.

        Returns:
            Texte avec codes ANSI si TTY, texte brut sinon.
        """
        if not self._is_tty():
            return text
        color = self.ROOT_STYLE if is_root else self.USER_STYLE
        return f"{color}{text}{self.RESET}"

    def format_start(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le début d'exécution avec style ANSI."""
        cmd_str = " ".join(command)
        prefix = self._prefix(is_root)
        return self._apply_style(
            f"{prefix} Exécution : {cmd_str}", is_root
        )

    def format_start_streaming(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le début d'exécution streaming avec style ANSI."""
        cmd_str = " ".join(command)
        prefix = self._prefix(is_root)
        return self._apply_style(
            f"{prefix} Exécution (streaming) : {cmd_str}", is_root
        )

    def format_dry_run(
        self, command: List[str], is_root: bool
    ) -> str:
        """Formate le message de simulation avec style gris discret."""
        cmd_str = " ".join(command)
        prefix = self._prefix(is_root)
        text = f"{prefix} [dry-run] {cmd_str}"
        if self._is_tty():
            return f"{self.DRY_STYLE}{text}{self.RESET}"
        return text

    def format_line(
        self, line: str, is_root: bool
    ) -> str:
        """Retourne la ligne sans style (contenu brut préservé)."""
        return line
