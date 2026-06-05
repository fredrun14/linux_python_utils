"""Gestion des reservations DHCP statiques.

Ce module fournit l'implementation LinuxDhcpReservationManager
pour allouer des adresses IP fixes et exporter la configuration
dnsmasq.
"""

import dataclasses
from typing import List, Optional, Set

from linux_python_utils.logging.base import Logger
from linux_python_utils.network.base import (
    DhcpReservationManager,
)
from linux_python_utils.network.config import (
    DhcpRange,
    NetworkConfig,
)
from linux_python_utils.network.ip_utils import (
    _next_available_ip,
)
from linux_python_utils.network.models import NetworkDevice


class LinuxDhcpReservationManager(DhcpReservationManager):
    """Gestionnaire de reservations DHCP statiques.

    Attributes:
        _config: Configuration reseau.
        _logger: Logger optionnel.
    """

    def __init__(
        self,
        config: NetworkConfig,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initialise le gestionnaire DHCP.

        Args:
            config: Configuration reseau.
            logger: Logger optionnel.
        """
        self._config = config
        self._logger = logger

    def generate_reservations(
        self, devices: List[NetworkDevice]
    ) -> List[NetworkDevice]:
        """Alloue des IP fixes aux peripheriques.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Liste des peripheriques avec IP fixes.

        Raises:
            ValueError: Si la plage DHCP n'est pas configuree
                ou est epuisee.
        """
        if self._config.dhcp_range is None:
            raise ValueError(
                "Plage DHCP non configuree"
            )
        used_ips: Set[str] = {
            d.fixed_ip
            for d in devices
            if d.fixed_ip is not None
        }
        result: List[NetworkDevice] = []
        for device in devices:
            if device.fixed_ip is not None:
                result.append(device)
                continue
            ip = _next_available_ip(
                self._config.dhcp_range, used_ips
            )
            if ip is None:
                raise ValueError(
                    "Plage DHCP epuisee : plus d'IP "
                    "disponibles"
                )
            used_ips.add(ip)
            result.append(
                dataclasses.replace(
                    device, fixed_ip=ip
                )
            )
        if self._logger:
            self._logger.log_info(
                f"Reservations DHCP : {len(result)} "
                f"peripherique(s)"
            )
        return result

    def export_reservations(
        self, devices: List[NetworkDevice]
    ) -> str:
        """Exporte les reservations au format dnsmasq.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Configuration dnsmasq formatee.
        """
        lines = [
            "# Reservations DHCP statiques",
            "# Genere par scanNetHome",
        ]
        for device in devices:
            if device.fixed_ip is None:
                continue
            entry = f"dhcp-host={device.mac},{device.fixed_ip}"
            if device.hostname:
                entry += f",{device.hostname}"
            lines.append(entry)
        return "\n".join(lines) + "\n"
