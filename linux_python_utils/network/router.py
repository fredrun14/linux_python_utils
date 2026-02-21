"""Client HTTP pour le routeur ASUS RT-AX88U.

Ce module fournit l'acces a l'API locale du routeur ASUS
pour scanner les clients connectes, lire les baux DHCP et
pousser les reservations statiques directement sur le routeur.

Credentials requis via variables d'environnement :
    ASUS_ROUTER_USER     (defaut : admin)
    ASUS_ROUTER_PASSWORD (defaut : chaine vide)
"""

import base64
import dataclasses
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from linux_python_utils.logging.base import Logger
from linux_python_utils.network.base import (
    NetworkScanner,
    RouterDhcpManager,
)
from linux_python_utils.network.config import (
    DhcpRange,
    NetworkConfig,
)
from linux_python_utils.network.models import NetworkDevice


# ---------------------------------------------------------------------------
# Helpers prives (reutilises par AsusRouterDhcpManager)
# ---------------------------------------------------------------------------

def _ip_to_int(ip: str) -> int:
    """Convertit une adresse IPv4 en entier.

    Args:
        ip: Adresse IPv4.

    Returns:
        Representation entiere.
    """
    parts = [int(o) for o in ip.split(".")]
    return (
        (parts[0] << 24)
        + (parts[1] << 16)
        + (parts[2] << 8)
        + parts[3]
    )


def _int_to_ip(num: int) -> str:
    """Convertit un entier en adresse IPv4.

    Args:
        num: Representation entiere.

    Returns:
        Adresse IPv4.
    """
    return (
        f"{(num >> 24) & 0xFF}."
        f"{(num >> 16) & 0xFF}."
        f"{(num >> 8) & 0xFF}."
        f"{num & 0xFF}"
    )


_VENDOR_TYPES: Tuple = (
    ("synology", "NAS"),
    ("nvidia", "Media Player"),
    ("nintendo", "Console"),
    ("apple", "Apple"),
    ("oneplus", "Smartphone"),
    ("samsung", "Smartphone"),
    ("huawei", "Smartphone"),
    ("xiaomi", "Smartphone"),
    ("asustek", "Routeur"),
    ("philips light", "Eclairage"),
    ("philips hue", "Eclairage"),
    ("hangzhou", "Camera/IoT"),
    ("hikvision", "Camera"),
    ("amazon", "Amazon"),
    ("raspberry", "Raspberry Pi"),
    ("sonos", "Audio"),
    ("espressif", "IoT"),
    ("intel", "PC/Laptop"),
    ("realtek", "PC/Laptop"),
)


def _infer_type_from_vendor(vendor: str) -> str:
    """Infere le type d'appareil depuis le fabricant.

    Args:
        vendor: Nom du fabricant (OUI ou DPI).

    Returns:
        Type infere ou 'unknown'.
    """
    v = vendor.lower()
    for keyword, device_type in _VENDOR_TYPES:
        if keyword in v:
            return device_type
    return "unknown"


def _parse_nvram_reservations(
    static_list: str,
    hostnames_str: str,
) -> Dict[str, Tuple[str, str]]:
    """Parse les chaines NVRAM en dict de reservations.

    Supporte les formats ancien et nouveau firmware :
    - Ancien : <MAC>IP<MAC>IP...
    - Nouveau (386+) : <MAC>IP>DNS>HOSTNAME<MAC>...

    Args:
        static_list: Chaine NVRAM dhcp_staticlist.
        hostnames_str: Chaine NVRAM dhcp_hostnames.

    Returns:
        Dict {mac_lowercase: (fixed_ip, dns_name)}.
    """
    hostnames: Dict[str, str] = {
        m.group(1).lower(): m.group(2).split(">")[0]
        for m in re.finditer(
            r"<([^>]+)>([^<]*)", hostnames_str
        )
    }
    result: Dict[str, Tuple[str, str]] = {}
    for match in re.finditer(
        r"<([^>]+)>([^<]*)", static_list
    ):
        mac = match.group(1).lower()
        # Format nouveau : IP>DNS>HOSTNAME — on prend le 1er champ
        fields = match.group(2).split(">")
        ip = fields[0].strip()
        # Le nom DNS peut etre dans le champ 4 (index 3)
        dns_from_nvram = (
            fields[3].strip()
            if len(fields) > 3
            else ""
        )
        if ip:
            result[mac] = (
                ip,
                dns_from_nvram or hostnames.get(mac, ""),
            )
    return result


def _next_available_ip(
    dhcp_range: DhcpRange, used_ips: Set[str]
) -> Optional[str]:
    """Trouve la prochaine IP libre dans la plage DHCP.

    Args:
        dhcp_range: Plage DHCP.
        used_ips: Ensemble des IP deja utilisees.

    Returns:
        Prochaine IP libre, ou None si plage epuisee.
    """
    start = _ip_to_int(dhcp_range.start)
    end = _ip_to_int(dhcp_range.end)
    for num in range(start, end + 1):
        ip = _int_to_ip(num)
        if ip not in used_ips:
            return ip
    return None


# ---------------------------------------------------------------------------
# Exceptions et configuration
# ---------------------------------------------------------------------------

class RouterAuthError(RuntimeError):
    """Erreur d'authentification au routeur ASUS."""


@dataclass(frozen=True)
class RouterConfig:
    """Configuration de connexion au routeur ASUS.

    Attributes:
        url: URL de base du routeur (http ou https).
        timeout: Timeout des requetes HTTP en secondes.
    """

    url: str = "http://192.168.50.1"
    timeout: int = 30

    def __post_init__(self) -> None:
        """Valide la configuration.

        Raises:
            ValueError: Si url ou timeout sont invalides.
        """
        if not self.url.startswith("http"):
            raise ValueError(
                f"URL invalide : {self.url!r}"
            )
        if self.timeout <= 0:
            raise ValueError(
                f"Timeout invalide : {self.timeout}"
            )


# ---------------------------------------------------------------------------
# Client HTTP bas niveau
# ---------------------------------------------------------------------------

class AsusRouterClient:
    """Client HTTP pour l'API locale du routeur ASUS.

    Attributes:
        _config: Configuration de connexion.
        _logger: Logger optionnel.
        _token: Token de session asus_token.
    """

    _HEADERS: Dict[str, str] = {
        "User-Agent": (
            "asusrouter-Android-DUTUtil-1.0.0.245"
        ),
        "Content-Type": (
            "application/x-www-form-urlencoded"
        ),
    }

    def __init__(
        self,
        config: RouterConfig,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initialise le client HTTP.

        Args:
            config: Configuration de connexion.
            logger: Logger optionnel.
        """
        self._config = config
        self._logger = logger
        self._token: Optional[str] = None

    def login(
        self, username: str, password: str
    ) -> None:
        """Authentifie la session sur le routeur.

        Args:
            username: Nom d'utilisateur.
            password: Mot de passe.

        Raises:
            RouterAuthError: Si l'authentification echoue.
        """
        credentials = base64.b64encode(
            f"{username}:{password}".encode("ascii")
        ).decode("ascii")
        data = urllib.parse.urlencode(
            {"login_authorization": credentials}
        ).encode("ascii")
        req = urllib.request.Request(
            f"{self._config.url}/login.cgi",
            data=data,
            headers=self._HEADERS,
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                req, timeout=self._config.timeout
            ) as resp:
                body = json.loads(
                    resp.read().decode("utf-8")
                )
        except Exception as exc:
            raise RouterAuthError(
                f"Connexion echouee : {exc}"
            ) from exc
        token = body.get("asus_token")
        if not token:
            raise RouterAuthError(
                "Token absent de la reponse login"
            )
        self._token = token
        if self._logger:
            self._logger.log_info(
                "Authentification routeur reussie"
            )

    def logout(self) -> None:
        """Ferme la session sur le routeur."""
        if not self._token:
            return
        req = urllib.request.Request(
            f"{self._config.url}/Logout.asp",
            headers={
                **self._HEADERS,
                "Cookie": f"asus_token={self._token}",
            },
            method="GET",
        )
        try:
            urllib.request.urlopen(
                req, timeout=self._config.timeout
            )
        except Exception:
            pass
        finally:
            self._token = None

    def _require_token(self) -> str:
        """Retourne le token actif.

        Returns:
            Token de session.

        Raises:
            RouterAuthError: Si non authentifie.
        """
        if not self._token:
            raise RouterAuthError(
                "Non authentifie : appeler login() d'abord"
            )
        return self._token

    def _hook(self, hook: str) -> dict:
        """Envoie une requete hook vers /appGet.cgi.

        Args:
            hook: Expression hook ASUS.

        Returns:
            Reponse JSON parsee.

        Raises:
            RouterAuthError: Si non authentifie.
            RuntimeError: Si la requete echoue.
        """
        token = self._require_token()
        data = urllib.parse.urlencode(
            {"hook": hook}
        ).encode("ascii")
        req = urllib.request.Request(
            f"{self._config.url}/appGet.cgi",
            data=data,
            headers={
                **self._HEADERS,
                "Cookie": f"asus_token={token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                req, timeout=self._config.timeout
            ) as resp:
                return json.loads(
                    resp.read().decode("utf-8")
                )
        except Exception as exc:
            raise RuntimeError(
                f"Echec requete hook '{hook}' : {exc}"
            ) from exc

    def get_clients(self) -> List[dict]:
        """Retourne les clients connectes (isOnline==1).

        Returns:
            Liste de dicts avec mac, ip, name, vendor.
        """
        data = self._hook("get_clientlist(appobj)")
        clients_raw = data.get("get_clientlist", data)
        if not isinstance(clients_raw, dict):
            return []
        return [
            {"mac": mac, **info}
            for mac, info in clients_raw.items()
            if len(mac) == 17
            and isinstance(info, dict)
            and info.get("isOnline") == "1"
        ]

    def get_dhcp_leases(self) -> Dict[str, str]:
        """Retourne les baux DHCP actifs sous forme mac→ip.

        Returns:
            Dictionnaire {mac_lowercase: ip}.
        """
        data = self._hook("dhcpLeaseMacList()")
        raw = data.get("dhcpLeaseMacList", "")
        leases: Dict[str, str] = {}
        for line in str(raw).strip().split("\n"):
            parts = line.strip().split()
            # Format dnsmasq : timestamp mac ip hostname cid
            if len(parts) >= 3:
                mac = parts[1].lower()
                ip = parts[2]
                if len(mac) == 17 and ip != "*":
                    leases[mac] = ip
        return leases

    def get_nvram(self, *keys: str) -> Dict[str, str]:
        """Lit des variables NVRAM du routeur.

        Args:
            *keys: Noms de variables NVRAM.

        Returns:
            Dictionnaire {cle: valeur}.
        """
        hook = ";".join(
            f"nvram_get({k})" for k in keys
        )
        return self._hook(hook)

    def set_static_reservations(
        self,
        static_list: str,
        hostnames: str,
        dhcp_cfg: Dict[str, str],
    ) -> None:
        """Envoie les reservations DHCP statiques au routeur.

        Args:
            static_list: Format NVRAM <MAC>IP<MAC>IP...
            hostnames: Format NVRAM <MAC>hostname...
            dhcp_cfg: Valeurs DHCP actuelles du routeur.

        Raises:
            RouterAuthError: Si non authentifie.
            RuntimeError: Si l'envoi echoue.
        """
        token = self._require_token()
        payload = {
            "current_page": (
                "Advanced_DHCP_Content.asp"
            ),
            "next_page": "",
            "action_mode": "apply",
            "action_script": "restart_dnsmasq",
            "action_wait": "5",
            "dhcp_enable_x": dhcp_cfg.get(
                "dhcp_enable_x", "1"
            ),
            "dhcp_start": dhcp_cfg.get(
                "dhcp_start", ""
            ),
            "dhcp_end": dhcp_cfg.get("dhcp_end", ""),
            "dhcp_lease": dhcp_cfg.get(
                "dhcp_lease", "86400"
            ),
            "dhcp_static_x": "1",
            "dhcp_staticlist": static_list,
            "dhcp_hostnames": hostnames,
        }
        data = urllib.parse.urlencode(
            payload
        ).encode("ascii")
        req = urllib.request.Request(
            f"{self._config.url}/start_apply.htm",
            data=data,
            headers={
                **self._HEADERS,
                "Cookie": f"asus_token={token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                req, timeout=self._config.timeout
            ) as resp:
                status = resp.status
        except Exception as exc:
            raise RuntimeError(
                f"Echec envoi reservations DHCP : {exc}"
            ) from exc
        if status not in (200, 302):
            raise RuntimeError(
                f"Reponse inattendue : HTTP {status}"
            )
        if self._logger:
            self._logger.log_info(
                "Reservations DHCP appliquees sur le routeur"
            )


# ---------------------------------------------------------------------------
# Scanner via API routeur
# ---------------------------------------------------------------------------

class AsusRouterScanner(NetworkScanner):
    """Scanner reseau via l'API locale du routeur ASUS.

    Ne necessite pas de privileges root.
    Credentials lus depuis ASUS_ROUTER_USER et
    ASUS_ROUTER_PASSWORD.

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
        username = os.environ.get(
            "ASUS_ROUTER_USER", "admin"
        )
        password = os.environ.get(
            "ASUS_ROUTER_PASSWORD", ""
        )
        self._client.login(username, password)
        try:
            raw_clients = self._client.get_clients()
            leases = self._client.get_dhcp_leases()
            nvram = self._client.get_nvram(
                "dhcp_staticlist", "dhcp_hostnames"
            )
            reservations = _parse_nvram_reservations(
                nvram.get("dhcp_staticlist", ""),
                nvram.get("dhcp_hostnames", ""),
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
            if not ip or ip == "0.0.0.0":
                ip = leases.get(mac, "")
            if not ip:
                continue
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


# ---------------------------------------------------------------------------
# Gestionnaire DHCP avec push vers le routeur
# ---------------------------------------------------------------------------

class AsusRouterDhcpManager(RouterDhcpManager):
    """Gestionnaire DHCP avec push direct vers le routeur ASUS.

    Attributes:
        _config: Configuration reseau.
        _router_config: Configuration routeur.
        _logger: Logger optionnel.
        _client: Client HTTP.
    """

    def __init__(
        self,
        config: NetworkConfig,
        router_config: RouterConfig,
        logger: Optional[Logger] = None,
        client: Optional[AsusRouterClient] = None,
    ) -> None:
        """Initialise le gestionnaire DHCP routeur.

        Args:
            config: Configuration reseau.
            router_config: Configuration de connexion.
            logger: Logger optionnel.
            client: Client HTTP optionnel (injection).
        """
        self._config = config
        self._router_config = router_config
        self._logger = logger
        self._client = client or AsusRouterClient(
            router_config, logger=logger
        )

    def generate_reservations(
        self, devices: List[NetworkDevice]
    ) -> List[NetworkDevice]:
        """Alloue des IP fixes depuis la plage DHCP.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Liste avec IP fixes assignees.

        Raises:
            ValueError: Si la plage DHCP manque ou est
                epuisee.
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
                    "Plage DHCP epuisee"
                )
            used_ips.add(ip)
            result.append(
                dataclasses.replace(device, fixed_ip=ip)
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
        """Exporte les reservations au format NVRAM ASUS.

        Format : <MAC>IP<MAC>IP...
        MAC en majuscules avec ':'.

        Args:
            devices: Liste des peripheriques.

        Returns:
            Chaine dhcp_staticlist.
        """
        parts = []
        for device in devices:
            if device.fixed_ip is None:
                continue
            mac = device.mac.upper()
            parts.append(f"<{mac}>{device.fixed_ip}")
        return "".join(parts)

    def apply_reservations(
        self, devices: List[NetworkDevice]
    ) -> None:
        """Envoie les reservations DHCP vers le routeur.

        Lit la configuration DHCP actuelle du routeur avant
        d'envoyer pour eviter d'ecraser les autres parametres.

        Args:
            devices: Peripheriques avec fixed_ip.

        Raises:
            RouterAuthError: Si l'authentification echoue.
            RuntimeError: Si l'envoi echoue.
        """
        username = os.environ.get(
            "ASUS_ROUTER_USER", "admin"
        )
        password = os.environ.get(
            "ASUS_ROUTER_PASSWORD", ""
        )
        self._client.login(username, password)
        try:
            dhcp_cfg = self._client.get_nvram(
                "dhcp_enable_x",
                "dhcp_start",
                "dhcp_end",
                "dhcp_lease",
                "dhcp_static_x",
            )
            static_list, hostnames = (
                self._build_nvram_strings(devices)
            )
            self._client.set_static_reservations(
                static_list, hostnames, dhcp_cfg
            )
        finally:
            self._client.logout()
        if self._logger:
            count = sum(
                1
                for d in devices
                if d.fixed_ip is not None
            )
            self._logger.log_info(
                f"{count} reservation(s) DHCP "
                f"appliquee(s) sur le routeur"
            )

    def read_reservations(self) -> List[NetworkDevice]:
        """Lit les reservations DHCP existantes du routeur.

        Returns:
            Liste de NetworkDevice avec ip et mac.

        Raises:
            RouterAuthError: Si l'authentification echoue.
        """
        username = os.environ.get(
            "ASUS_ROUTER_USER", "admin"
        )
        password = os.environ.get(
            "ASUS_ROUTER_PASSWORD", ""
        )
        self._client.login(username, password)
        try:
            nvram = self._client.get_nvram(
                "dhcp_staticlist",
                "dhcp_hostnames",
            )
        finally:
            self._client.logout()
        return self._parse_nvram_staticlist(
            nvram.get("dhcp_staticlist", ""),
            nvram.get("dhcp_hostnames", ""),
        )

    def _build_nvram_strings(
        self, devices: List[NetworkDevice]
    ) -> Tuple[str, str]:
        """Construit les chaines NVRAM dhcp_staticlist et
        dhcp_hostnames.

        Args:
            devices: Peripheriques avec fixed_ip.

        Returns:
            Tuple (static_list, hostnames).
        """
        static_parts: List[str] = []
        hostname_parts: List[str] = []
        for device in devices:
            if device.fixed_ip is None:
                continue
            mac = device.mac.upper()
            static_parts.append(
                f"<{mac}>{device.fixed_ip}"
            )
            name = device.hostname or device.dns_name
            if name:
                hostname_parts.append(f"<{mac}>{name}")
        return (
            "".join(static_parts),
            "".join(hostname_parts),
        )

    @staticmethod
    def _parse_nvram_staticlist(
        static_list: str,
        hostnames_str: str,
    ) -> List[NetworkDevice]:
        """Parse la chaine NVRAM dhcp_staticlist.

        Args:
            static_list: Chaine <MAC>IP<MAC>IP...
            hostnames_str: Chaine <MAC>hostname...

        Returns:
            Liste de NetworkDevice.
        """
        reservations = _parse_nvram_reservations(
            static_list, hostnames_str
        )
        devices: List[NetworkDevice] = []
        for mac, (ip, hostname) in reservations.items():
            try:
                devices.append(
                    NetworkDevice(
                        ip=ip,
                        mac=mac,
                        fixed_ip=ip,
                        hostname=hostname,
                    )
                )
            except ValueError:
                continue
        return devices
