"""Interfaces abstraites pour le module reseau.

Ce module definit les classes de base abstraites (ABCs) pour
le scan reseau, la persistance, la gestion DHCP/DNS et les
rapports.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from linux_python_utils.network.config import NetworkConfig
from linux_python_utils.network.models import NetworkDevice


class NetworkScanner(ABC):
    """Interface pour les scanners reseau."""

    @abstractmethod
    def scan(
        self, config: NetworkConfig
    ) -> List[NetworkDevice]:
        """Scanne le reseau et retourne les peripheriques.

        Args:
            config: Configuration reseau.

        Returns:
            Liste des peripheriques decouverts.
        """
        pass


class DeviceRepository(ABC):
    """Interface pour la persistance des peripheriques."""

    @abstractmethod
    def load(self) -> List[NetworkDevice]:
        """Charge les peripheriques depuis le stockage.

        Returns:
            Liste des peripheriques.
        """
        pass

    @abstractmethod
    def save(
        self, devices: List[NetworkDevice]
    ) -> None:
        """Sauvegarde les peripheriques.

        Args:
            devices: Liste des peripheriques a sauvegarder.
        """
        pass

    @abstractmethod
    def find_by_mac(
        self, mac: str
    ) -> Optional[NetworkDevice]:
        """Recherche un peripherique par adresse MAC.

        Args:
            mac: Adresse MAC a rechercher.

        Returns:
            Le peripherique trouve ou None.
        """
        pass

    @abstractmethod
    def find_by_ip(
        self, ip: str
    ) -> Optional[NetworkDevice]:
        """Recherche un peripherique par adresse IP.

        Args:
            ip: Adresse IP a rechercher.

        Returns:
            Le peripherique trouve ou None.
        """
        pass


class DhcpReservationManager(ABC):
    """Interface pour la gestion des reservations DHCP."""

    @abstractmethod
    def generate_reservations(
        self, devices: List[NetworkDevice]
    ) -> List[NetworkDevice]:
        """Genere les reservations DHCP pour les peripheriques.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Liste des peripheriques avec IP fixes assignees.
        """
        pass

    @abstractmethod
    def export_reservations(
        self, devices: List[NetworkDevice]
    ) -> str:
        """Exporte les reservations au format texte.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Reservations formatees.
        """
        pass


class RouterDhcpManager(DhcpReservationManager):
    """Interface DHCP avec application directe au routeur."""

    @abstractmethod
    def apply_reservations(
        self, devices: List[NetworkDevice]
    ) -> None:
        """Envoie les reservations DHCP vers le routeur.

        Args:
            devices: Peripheriques avec IP fixes assignees.
        """
        pass

    @abstractmethod
    def read_reservations(self) -> List[NetworkDevice]:
        """Lit les reservations DHCP existantes du routeur.

        Returns:
            Liste des peripheriques reserves.
        """
        pass


class DnsManager(ABC):
    """Interface pour la gestion DNS locale."""

    @abstractmethod
    def generate_dns_names(
        self, devices: List[NetworkDevice]
    ) -> List[NetworkDevice]:
        """Genere les noms DNS pour les peripheriques.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Liste des peripheriques avec noms DNS.
        """
        pass

    @abstractmethod
    def generate_hosts_entries(
        self, devices: List[NetworkDevice]
    ) -> str:
        """Genere les entrees pour le fichier hosts.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Contenu du fichier hosts.
        """
        pass


class DeviceReporter(ABC):
    """Interface pour les rapports de peripheriques."""

    @abstractmethod
    def report(
        self, devices: List[NetworkDevice]
    ) -> str:
        """Genere un rapport des peripheriques.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Rapport formate.
        """
        pass
