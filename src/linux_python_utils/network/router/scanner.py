"""Scanner reseau via l'API locale du routeur ASUS."""

from typing import Dict, List, Optional, Tuple

from linux_python_utils.logging.base import Logger
from linux_python_utils.network.base import NetworkScanner
from linux_python_utils.network.config import NetworkConfig
from linux_python_utils.network.models import NetworkDevice
from linux_python_utils.network.router._nvram import (
    _parse_custom_clientlist,
    _parse_nvram_reservations,
)
from linux_python_utils.network.router.client import (
    AsusRouterClient,
    RouterConfig,
)
from linux_python_utils.network.vendors import (
    _infer_type_from_vendor,
)


class AsusRouterScanner(NetworkScanner):
    """Scanner reseau via l'API locale du routeur ASUS.

    Ne necessite pas de privileges root.
    Les credentials sont passes via RouterConfig.

    Attributes:
        _router_config: Configuration routeur.
        _logger: Logger optionnel.
        _client: Client HTTP.
    """

    def __init__(
        self,
        router_config: RouterConfig,
        logger: Optional[Logger] = None,
        client: Optional[AsusRouterClient] = None,
    ) -> None:
        """Initialise le scanner routeur.

        Args:
            router_config: Configuration de connexion.
            logger: Logger optionnel.
            client: Client HTTP optionnel (injection).
        """
        self._router_config = router_config
        self._logger = logger
        self._client = client or AsusRouterClient(
            router_config, logger=logger
        )

    def scan(
        self, config: NetworkConfig
    ) -> List[NetworkDevice]:
        """Scanne le reseau via l'API du routeur.

        Args:
            config: Configuration reseau (parametre ABC,
                non utilise pour la requete HTTP).

        Returns:
            Liste des peripheriques connectes.

        Raises:
            RouterAuthError: Si l'authentification echoue.
            RuntimeError: Si la requete echoue.
        """
        self._client.login(
            self._router_config.username,
            self._router_config.password,
        )
        try:
            raw_clients = self._client.get_clients()
            leases = self._client.get_dhcp_leases()
            nvram = self._client.get_nvram(
                "dhcp_staticlist",
                "dhcp_hostnames",
                "custom_clientlist",
            )
            reservations = _parse_nvram_reservations(
                nvram.get("dhcp_staticlist", ""),
                nvram.get("dhcp_hostnames", ""),
            )
            custom_clients = _parse_custom_clientlist(
                nvram.get("custom_clientlist", "")
            )
            raw_clients = self._merge_offline_clients(
                raw_clients,
                custom_clients,
                leases,
                reservations,
            )
            devices = self._parse_clients(
                raw_clients, leases, reservations
            )
        finally:
            self._client.logout()
        if self._logger:
            self._logger.log_info(
                f"Routeur : {len(devices)} "
                f"peripherique(s) decouvert(s)"
            )
        return devices

    def _merge_offline_clients(
        self,
        raw_clients: List[dict],
        custom_clients: Dict[str, str],
        leases: Dict[str, str],
        reservations: Dict[str, Tuple[str, str]],
    ) -> List[dict]:
        """Ajoute les clients offline depuis custom_clientlist.

        Les clients deja presents dans raw_clients (online)
        sont conserves tels quels. Les clients memorises
        dans custom_clientlist mais absents de raw_clients
        sont ajoutes comme entrees offline si leur IP est
        connue (bail DHCP ou reservation statique).

        Args:
            raw_clients: Clients online retournes par
                get_clientlist.
            custom_clients: Dict {mac: nickname} depuis
                custom_clientlist NVRAM.
            leases: Dict {mac: ip} des baux DHCP actifs.
            reservations: Dict {mac: (fixed_ip, dns_name)}
                des reservations statiques.

        Returns:
            Liste etendue incluant les clients offline.
        """
        online_macs: set = {
            c.get("mac", "").lower()
            for c in raw_clients
        }
        result = list(raw_clients)
        for mac, nickname in custom_clients.items():
            if mac in online_macs:
                continue
            ip = leases.get(mac, "")
            if not ip:
                fixed, _ = reservations.get(
                    mac, (None, None)
                )
                ip = fixed or ""
            result.append(
                {
                    "mac": mac,
                    "ip": ip,
                    "isOnline": "0",
                    "nickName": nickname,
                    "vendor": "",
                    "dpiDevice": "",
                    "ipMethod": (
                        "Manual"
                        if mac in reservations
                        else ""
                    ),
                }
            )
        return result

    def _parse_clients(
        self,
        raw: List[dict],
        leases: Dict[str, str],
        reservations: Optional[
            Dict[str, Tuple[str, str]]
        ] = None,
    ) -> List[NetworkDevice]:
        """Parse les clients bruts en NetworkDevice.

        Utilise nickName > name pour le hostname,
        dpiDevice pour le type, et les reservations DHCP
        statiques pour fixed_ip et dns_name.

        Args:
            raw: Liste de dicts clients du routeur.
            leases: Dict {mac_lowercase: ip} des baux DHCP.
            reservations: Dict {mac: (fixed_ip, dns_name)}
                des reservations statiques du routeur.

        Returns:
            Liste de NetworkDevice valides.
        """
        if reservations is None:
            reservations = {}
        devices: List[NetworkDevice] = []
        for client in raw:
            mac = client.get("mac", "").lower()
            if len(mac) != 17:
                continue
            ip = client.get("ip", "")
            if not ip or ip == "0.0.0.0":  # nosec B104
                ip = leases.get(mac, "")
            if not ip:
                # Dernier recours : IP fixe de la
                # reservation statique (appareils offline
                # sans bail DHCP actif)
                fixed_ip_fallback, _ = reservations.get(
                    mac, (None, None)
                )
                ip = fixed_ip_fallback or ""
            # nickName = nom personnalise dans l'UI routeur
            # name = hostname DHCP envoye par l'appareil
            hostname = (
                client.get("nickName", "").strip()
                or client.get("name", "").strip()
            )
            vendor = client.get("vendor", "")
            # dpiDevice = type DPI du routeur, sinon vendor
            device_type = (
                client.get("dpiDevice", "").strip()
                or _infer_type_from_vendor(vendor)
            )
            fixed_ip, dns_name = reservations.get(
                mac, (None, None)
            )
            # ipMethod=="Manual" : IP fixee dans le routeur
            if not fixed_ip and (
                client.get("ipMethod", "") == "Manual"
            ):
                fixed_ip = ip
            try:
                devices.append(
                    NetworkDevice(
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        vendor=vendor,
                        device_type=device_type,
                        fixed_ip=fixed_ip,
                        dns_name=dns_name,
                    )
                )
            except ValueError:
                continue
        return devices
