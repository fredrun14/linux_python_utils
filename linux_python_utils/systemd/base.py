"""Interface abstraite pour la gestion des services systemd."""

from abc import ABC, abstractmethod


class SystemdServiceManager(ABC):
    """Interface pour la gestion des services systemd."""

    @abstractmethod
    def enable_timer(self, timer_name: str) -> bool:
        """
        Active et démarre un timer systemd.

        Args:
            timer_name: Nom du timer (ex: "flatpak-update.timer")

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def reload_systemd(self) -> bool:
        """
        Recharge la configuration systemd (daemon-reload).

        Returns:
            True si succès, False sinon
        """
        pass
