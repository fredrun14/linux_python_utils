"""Module reseau pour la gestion des peripheriques.

Ce module fournit les outils pour scanner, inventorier et
gerer les peripheriques d'un reseau local.
"""

from linux_python_utils.network.base import (
    DeviceReporter,
    DeviceRepository,
    DhcpReservationManager,
    DnsManager,
    NetworkScanner,
    RouterDhcpManager,
)
from linux_python_utils.network.config import (
    DhcpRange,
    DnsConfig,
    NetworkConfig,
)
from linux_python_utils.network.dhcp import (
    LinuxDhcpReservationManager,
)
from linux_python_utils.network.dns import (
    LinuxDnsmasqConfigGenerator,
    LinuxHostsFileManager,
)
from linux_python_utils.network.models import (
    NetworkDevice,
)
from linux_python_utils.network.reporter import (
    ConsoleTableReporter,
    CsvReporter,
    DiffReporter,
    JsonReporter,
)
from linux_python_utils.network.repository import (
    JsonDeviceRepository,
)
from linux_python_utils.network.router import (
    AsusRouterClient,
    AsusRouterDhcpManager,
    AsusRouterScanner,
    RouterAuthError,
    RouterConfig,
)
from linux_python_utils.network.scanner import (
    LinuxArpScanner,
    LinuxNmapScanner,
)
from linux_python_utils.network.validators import (
    validate_cidr,
    validate_hostname,
    validate_ipv4,
    validate_mac,
)

__all__ = [
    # Modeles
    "NetworkDevice",
    # Configuration
    "NetworkConfig",
    "DhcpRange",
    "DnsConfig",
    # ABCs
    "NetworkScanner",
    "DeviceRepository",
    "DhcpReservationManager",
    "RouterDhcpManager",
    "DnsManager",
    "DeviceReporter",
    # Scanners
    "LinuxArpScanner",
    "LinuxNmapScanner",
    # Routeur ASUS
    "RouterConfig",
    "RouterAuthError",
    "AsusRouterClient",
    "AsusRouterScanner",
    "AsusRouterDhcpManager",
    # Repository
    "JsonDeviceRepository",
    # DHCP
    "LinuxDhcpReservationManager",
    # DNS
    "LinuxHostsFileManager",
    "LinuxDnsmasqConfigGenerator",
    # Rapports
    "ConsoleTableReporter",
    "CsvReporter",
    "JsonReporter",
    "DiffReporter",
    # Validateurs
    "validate_ipv4",
    "validate_mac",
    "validate_cidr",
    "validate_hostname",
]
