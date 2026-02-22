"""Tests pour le module router (AsusRouterClient et AsusRouterScanner).

Valide en particulier que les appareils offline (isOnline==0)
sont bien inclus dans les resultats du scan.
"""

from unittest.mock import MagicMock

import pytest

from linux_python_utils.network.config import NetworkConfig, DhcpRange
from linux_python_utils.network.router import (
    AsusRouterClient,
    AsusRouterScanner,
    RouterConfig,
    _parse_custom_clientlist,
    _parse_nvram_reservations,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router_config() -> RouterConfig:
    """Configuration routeur de test."""
    return RouterConfig(
        url="http://192.168.50.1",
        timeout=10,
        username="admin",
        password="secret",
    )


@pytest.fixture
def network_config() -> NetworkConfig:
    """Configuration reseau de test."""
    return NetworkConfig(
        cidr="192.168.50.0/24",
        dhcp_range=DhcpRange(
            start="192.168.50.100",
            end="192.168.50.254",
        ),
    )


@pytest.fixture
def mock_client() -> MagicMock:
    """Client HTTP mocke."""
    return MagicMock(spec=AsusRouterClient)


@pytest.fixture
def scanner(
    router_config: RouterConfig,
    mock_client: MagicMock,
) -> AsusRouterScanner:
    """Scanner avec client HTTP mocke."""
    return AsusRouterScanner(
        router_config, client=mock_client
    )


# ---------------------------------------------------------------------------
# Donnees de test
# ---------------------------------------------------------------------------

_CLIENTS_ONLINE_ONLY = {
    "48:b0:2d:03:1e:ea": {
        "ip": "192.168.50.3",
        "isOnline": "1",
        "nickName": "Shield",
        "vendor": "NVIDIA Corporation",
        "dpiDevice": "AndroidTV",
        "ipMethod": "Manual",
    },
}

_CLIENTS_MIXED = {
    "48:b0:2d:03:1e:ea": {
        "ip": "192.168.50.3",
        "isOnline": "1",
        "nickName": "Shield",
        "vendor": "NVIDIA Corporation",
        "dpiDevice": "AndroidTV",
        "ipMethod": "Manual",
    },
    "58:16:d7:f1:77:6e": {
        "ip": "192.168.50.7",
        "isOnline": "0",
        "nickName": "Thermomix",
        "vendor": "Vorwerk",
        "dpiDevice": "",
        "ipMethod": "Manual",
    },
    "e2:b7:be:2b:bd:2f": {
        "ip": "192.168.50.15",
        "isOnline": "0",
        "nickName": "NanouIphone",
        "vendor": "Apple",
        "dpiDevice": "iPhone",
        "ipMethod": "",
    },
}

_CLIENTS_OFFLINE_NO_IP = {
    "dc:46:28:2f:ae:f4": {
        "ip": "0.0.0.0",
        "isOnline": "0",
        "nickName": "Asustuf5G",
        "vendor": "ASUSTeK",
        "dpiDevice": "",
        "ipMethod": "Manual",
    },
}

_CLIENTS_OFFLINE_STATIC_ONLY = {
    "7c:4d:8f:4c:a4:66": {
        "ip": "0.0.0.0",
        "isOnline": "0",
        "nickName": "print",
        "vendor": "HP",
        "dpiDevice": "",
        "ipMethod": "Manual",
    },
}


# ---------------------------------------------------------------------------
# Tests : _parse_custom_clientlist
# ---------------------------------------------------------------------------

class TestParseCustomClientlist:
    """Tests pour _parse_custom_clientlist."""

    def test_parse_entree_simple(self) -> None:
        """Une entree valide est correctement parsee."""
        raw = "<Shield>48:B0:2D:03:1E:EA>5>"
        result = _parse_custom_clientlist(raw)
        assert result == {"48:b0:2d:03:1e:ea": "Shield"}

    def test_parse_multiple_entrees(self) -> None:
        """Plusieurs entrees sont toutes parsees."""
        raw = (
            "<Shield>48:B0:2D:03:1E:EA>5>"
            "<Thermomix>58:16:D7:F1:77:6E>9>"
            "<NanouIphone>E2:B7:BE:2B:BD:2F>5>"
        )
        result = _parse_custom_clientlist(raw)
        assert len(result) == 3
        assert result["48:b0:2d:03:1e:ea"] == "Shield"
        assert result["58:16:d7:f1:77:6e"] == "Thermomix"
        assert result["e2:b7:be:2b:bd:2f"] == "NanouIphone"

    def test_mac_normalise_en_minuscules(self) -> None:
        """Les MACs sont normalises en minuscules."""
        raw = "<Test>AA:BB:CC:DD:EE:FF>0>"
        result = _parse_custom_clientlist(raw)
        assert "aa:bb:cc:dd:ee:ff" in result

    def test_entree_sans_nickname_ignoree(self) -> None:
        """Une entree avec nickname vide est ignoree."""
        raw = "<>48:B0:2D:03:1E:EA>5>"
        result = _parse_custom_clientlist(raw)
        assert result == {}

    def test_chaine_vide_retourne_dict_vide(self) -> None:
        """Une chaine vide retourne un dict vide."""
        result = _parse_custom_clientlist("")
        assert result == {}

    def test_mac_invalide_ignoree(self) -> None:
        """Une entree avec MAC invalide est ignoree."""
        raw = "<Test>GG:HH:II:JJ:KK:LL>0>"
        result = _parse_custom_clientlist(raw)
        assert result == {}

    def test_entites_html_decodees(self) -> None:
        """Les entites HTML &#60 et &#62 sont decodees."""
        raw = (
            "&#60print&#627C:4D:8F:4C:A4:66&#620&#62"
            "&#60REXCam&#6290:6A:94:4B:AD:2B&#620&#62"
        )
        result = _parse_custom_clientlist(raw)
        assert "7c:4d:8f:4c:a4:66" in result
        assert result["7c:4d:8f:4c:a4:66"] == "print"
        assert "90:6a:94:4b:ad:2b" in result
        assert result["90:6a:94:4b:ad:2b"] == "REXCam"


# ---------------------------------------------------------------------------
# Tests : AsusRouterScanner._merge_offline_clients
# ---------------------------------------------------------------------------

class TestMergeOfflineClients:
    """Tests pour _merge_offline_clients."""

    def test_client_online_non_duplique(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Un client online n'est pas ajoute en double."""
        raw = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
            }
        ]
        custom = {"48:b0:2d:03:1e:ea": "Shield"}
        leases: dict = {}
        reservations: dict = {}
        result = scanner._merge_offline_clients(
            raw, custom, leases, reservations
        )
        assert len(result) == 1

    def test_client_offline_ajoute_si_bail_connu(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Client offline avec bail DHCP actif est ajoute."""
        raw: list = []
        custom = {"58:16:d7:f1:77:6e": "Thermomix"}
        leases = {"58:16:d7:f1:77:6e": "192.168.50.7"}
        reservations: dict = {}
        result = scanner._merge_offline_clients(
            raw, custom, leases, reservations
        )
        assert len(result) == 1
        assert result[0]["mac"] == "58:16:d7:f1:77:6e"
        assert result[0]["ip"] == "192.168.50.7"
        assert result[0]["isOnline"] == "0"
        assert result[0]["nickName"] == "Thermomix"

    def test_client_offline_ajoute_si_reservation_statique(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Client offline avec reservation DHCP est ajoute."""
        raw: list = []
        custom = {"7c:4d:8f:4c:a4:66": "print"}
        leases: dict = {}
        reservations = {
            "7c:4d:8f:4c:a4:66": ("192.168.50.20", ""),
        }
        result = scanner._merge_offline_clients(
            raw, custom, leases, reservations
        )
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.50.20"
        assert result[0]["ipMethod"] == "Manual"

    def test_client_offline_inclus_sans_ip(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Client offline sans IP est inclus avec ip=''."""
        raw: list = []
        custom = {"aa:bb:cc:dd:ee:ff": "Inconnu"}
        leases: dict = {}
        reservations: dict = {}
        result = scanner._merge_offline_clients(
            raw, custom, leases, reservations
        )
        assert len(result) == 1
        assert result[0]["ip"] == ""
        assert result[0]["isOnline"] == "0"

    def test_fusion_online_et_offline(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Online et offline sont fusionnes correctement."""
        raw = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
            }
        ]
        custom = {
            "48:b0:2d:03:1e:ea": "Shield",
            "58:16:d7:f1:77:6e": "Thermomix",
        }
        leases = {"58:16:d7:f1:77:6e": "192.168.50.7"}
        reservations: dict = {}
        result = scanner._merge_offline_clients(
            raw, custom, leases, reservations
        )
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Tests : AsusRouterClient.get_clients
# ---------------------------------------------------------------------------

class TestAsusRouterClientGetClients:
    """Tests pour get_clients() sans filtre isOnline."""

    def _make_client(
        self, router_config: RouterConfig, raw_data: dict
    ) -> AsusRouterClient:
        """Cree un client avec _hook mocke."""
        client = AsusRouterClient(router_config)
        client._token = "fake-token"
        client._hook = MagicMock(
            return_value={"get_clientlist": raw_data}
        )
        return client

    def test_retourne_appareils_online(
        self, router_config: RouterConfig
    ) -> None:
        """Les appareils isOnline==1 sont toujours retournes."""
        client = self._make_client(
            router_config, _CLIENTS_ONLINE_ONLY
        )
        result = client.get_clients()
        assert len(result) == 1
        assert result[0]["mac"] == "48:b0:2d:03:1e:ea"

    def test_retourne_appareils_offline(
        self, router_config: RouterConfig
    ) -> None:
        """Les appareils isOnline==0 sont desormais inclus."""
        client = self._make_client(
            router_config, _CLIENTS_MIXED
        )
        result = client.get_clients()
        macs = {r["mac"] for r in result}
        assert "58:16:d7:f1:77:6e" in macs
        assert "e2:b7:be:2b:bd:2f" in macs

    def test_retourne_online_et_offline(
        self, router_config: RouterConfig
    ) -> None:
        """Online et offline sont retournes ensemble."""
        client = self._make_client(
            router_config, _CLIENTS_MIXED
        )
        result = client.get_clients()
        assert len(result) == 3

    def test_exclut_mac_invalide(
        self, router_config: RouterConfig
    ) -> None:
        """Les entrees avec MAC de mauvaise longueur sont ignorees."""
        data = {
            "INVALID": {"ip": "1.2.3.4", "isOnline": "0"},
            **_CLIENTS_ONLINE_ONLY,
        }
        client = self._make_client(router_config, data)
        result = client.get_clients()
        assert all(
            len(r["mac"]) == 17 for r in result
        )

    def test_exclut_valeur_non_dict(
        self, router_config: RouterConfig
    ) -> None:
        """Les valeurs non-dict sont ignorees."""
        data = {
            "48:b0:2d:03:1e:ea": "not-a-dict",
            "58:16:d7:f1:77:6e": {
                "ip": "192.168.50.7",
                "isOnline": "0",
                "nickName": "Thermomix",
            },
        }
        client = self._make_client(router_config, data)
        result = client.get_clients()
        assert len(result) == 1

    def test_hook_retourne_non_dict_retourne_vide(
        self, router_config: RouterConfig
    ) -> None:
        """Si le hook retourne une valeur invalide, liste vide."""
        client = AsusRouterClient(router_config)
        client._token = "fake-token"
        client._hook = MagicMock(
            return_value={"get_clientlist": "invalid"}
        )
        result = client.get_clients()
        assert result == []


# ---------------------------------------------------------------------------
# Tests : AsusRouterScanner._parse_clients
# ---------------------------------------------------------------------------

class TestAsusRouterScannerParseClients:
    """Tests pour _parse_clients avec cas offline."""

    def test_appareil_online_ip_directe(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Appareil online : IP issue du champ ip."""
        raw = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
                "vendor": "NVIDIA",
                "dpiDevice": "AndroidTV",
                "ipMethod": "Manual",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert len(result) == 1
        assert result[0].ip == "192.168.50.3"
        assert result[0].hostname == "Shield"

    def test_appareil_offline_avec_ip_connue(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Appareil offline dont le routeur connait la derniere IP."""
        raw = [
            {
                "mac": "58:16:d7:f1:77:6e",
                "ip": "192.168.50.7",
                "isOnline": "0",
                "nickName": "Thermomix",
                "vendor": "Vorwerk",
                "dpiDevice": "",
                "ipMethod": "Manual",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert len(result) == 1
        assert result[0].ip == "192.168.50.7"
        assert result[0].hostname == "Thermomix"

    def test_appareil_offline_ip_zero_fallback_bail_dhcp(
        self, scanner: AsusRouterScanner
    ) -> None:
        """IP=0.0.0.0 → fallback sur le bail DHCP actif."""
        raw = [
            {
                "mac": "dc:46:28:2f:ae:f4",
                "ip": "0.0.0.0",
                "isOnline": "0",
                "nickName": "Asustuf5G",
                "vendor": "ASUSTeK",
                "dpiDevice": "",
                "ipMethod": "",
            }
        ]
        leases = {"dc:46:28:2f:ae:f4": "192.168.50.18"}
        result = scanner._parse_clients(raw, leases, {})
        assert len(result) == 1
        assert result[0].ip == "192.168.50.18"

    def test_appareil_offline_ip_zero_fallback_reservation_statique(
        self, scanner: AsusRouterScanner
    ) -> None:
        """IP=0.0.0.0 et pas de bail → fallback reservation statique."""
        raw = [
            {
                "mac": "7c:4d:8f:4c:a4:66",
                "ip": "0.0.0.0",
                "isOnline": "0",
                "nickName": "print",
                "vendor": "HP",
                "dpiDevice": "",
                "ipMethod": "Manual",
            }
        ]
        reservations = {
            "7c:4d:8f:4c:a4:66": ("192.168.50.20", ""),
        }
        result = scanner._parse_clients(raw, {}, reservations)
        assert len(result) == 1
        assert result[0].ip == "192.168.50.20"

    def test_appareil_sans_ip_aucun_fallback_cree_avec_ip_vide(
        self, scanner: AsusRouterScanner
    ) -> None:
        """Appareil sans IP, sans bail, sans reservation : ip=''."""
        raw = [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "ip": "0.0.0.0",
                "isOnline": "0",
                "nickName": "Inconnu",
                "vendor": "",
                "dpiDevice": "",
                "ipMethod": "",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert len(result) == 1
        assert result[0].ip == ""
        assert result[0].hostname == "Inconnu"

    def test_mac_invalide_ignore(
        self, scanner: AsusRouterScanner
    ) -> None:
        """MAC de mauvaise longueur est ignoree."""
        raw = [
            {
                "mac": "invalid-mac",
                "ip": "192.168.50.99",
                "isOnline": "1",
                "nickName": "Test",
                "vendor": "",
                "dpiDevice": "",
                "ipMethod": "",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert result == []

    def test_nickname_prioritaire_sur_name(
        self, scanner: AsusRouterScanner
    ) -> None:
        """nickName est utilise en priorite sur name."""
        raw = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
                "name": "android-device",
                "vendor": "NVIDIA",
                "dpiDevice": "",
                "ipMethod": "",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert result[0].hostname == "Shield"

    def test_name_utilise_si_pas_de_nickname(
        self, scanner: AsusRouterScanner
    ) -> None:
        """name est utilise si nickName est absent."""
        raw = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "",
                "name": "android-device",
                "vendor": "NVIDIA",
                "dpiDevice": "",
                "ipMethod": "",
            }
        ]
        result = scanner._parse_clients(raw, {}, {})
        assert result[0].hostname == "android-device"


# ---------------------------------------------------------------------------
# Tests : AsusRouterScanner.scan (integration)
# ---------------------------------------------------------------------------

class TestAsusRouterScannerScan:
    """Tests d'integration pour scan() avec appareils offline."""

    def test_scan_retourne_client_online(
        self,
        scanner: AsusRouterScanner,
        mock_client: MagicMock,
        network_config: NetworkConfig,
    ) -> None:
        """scan() retourne les appareils online depuis get_clientlist."""
        mock_client.get_clients.return_value = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
                "vendor": "NVIDIA",
                "dpiDevice": "AndroidTV",
                "ipMethod": "Manual",
            },
        ]
        mock_client.get_dhcp_leases.return_value = {}
        mock_client.get_nvram.return_value = {
            "dhcp_staticlist": "",
            "dhcp_hostnames": "",
            "custom_clientlist": (
                "<Shield>48:B0:2D:03:1E:EA>5>"
            ),
        }

        result = scanner.scan(network_config)

        assert len(result) == 1
        assert result[0].mac == "48:b0:2d:03:1e:ea"

    def test_scan_inclut_client_offline_via_custom_clientlist(
        self,
        scanner: AsusRouterScanner,
        mock_client: MagicMock,
        network_config: NetworkConfig,
    ) -> None:
        """Appareil offline dans custom_clientlist + bail DHCP est inclus."""
        mock_client.get_clients.return_value = [
            {
                "mac": "48:b0:2d:03:1e:ea",
                "ip": "192.168.50.3",
                "isOnline": "1",
                "nickName": "Shield",
                "vendor": "NVIDIA",
                "dpiDevice": "AndroidTV",
                "ipMethod": "Manual",
            },
        ]
        mock_client.get_dhcp_leases.return_value = {
            "58:16:d7:f1:77:6e": "192.168.50.7",
        }
        mock_client.get_nvram.return_value = {
            "dhcp_staticlist": "",
            "dhcp_hostnames": "",
            "custom_clientlist": (
                "<Shield>48:B0:2D:03:1E:EA>5>"
                "<Thermomix>58:16:D7:F1:77:6E>9>"
            ),
        }

        result = scanner.scan(network_config)

        assert len(result) == 2
        macs = {d.mac for d in result}
        assert "48:b0:2d:03:1e:ea" in macs
        assert "58:16:d7:f1:77:6e" in macs
        thermo = next(
            d for d in result if d.mac == "58:16:d7:f1:77:6e"
        )
        assert thermo.hostname == "Thermomix"
        assert thermo.ip == "192.168.50.7"

    def test_scan_offline_utilise_reservation_statique(
        self,
        scanner: AsusRouterScanner,
        mock_client: MagicMock,
        network_config: NetworkConfig,
    ) -> None:
        """Appareil offline sans bail DHCP utilise la reservation NVRAM."""
        mock_client.get_clients.return_value = []
        mock_client.get_dhcp_leases.return_value = {}
        mock_client.get_nvram.return_value = {
            "dhcp_staticlist": (
                "<7C:4D:8F:4C:A4:66>192.168.50.20"
            ),
            "dhcp_hostnames": "",
            "custom_clientlist": (
                "<print>7C:4D:8F:4C:A4:66>1>"
            ),
        }

        result = scanner.scan(network_config)

        assert len(result) == 1
        assert result[0].ip == "192.168.50.20"
        assert result[0].fixed_ip == "192.168.50.20"
        assert result[0].hostname == "print"

    def test_scan_utilise_credentials_du_routerconfig(
        self,
        scanner: AsusRouterScanner,
        mock_client: MagicMock,
        network_config: NetworkConfig,
    ) -> None:
        """scan() utilise directement les credentials de RouterConfig."""
        mock_client.get_clients.return_value = []
        mock_client.get_dhcp_leases.return_value = {}
        mock_client.get_nvram.return_value = {
            "dhcp_staticlist": "",
            "dhcp_hostnames": "",
            "custom_clientlist": "",
        }

        scanner.scan(network_config)

        mock_client.login.assert_called_once_with(
            "admin", "secret"
        )

    def test_scan_appelle_logout_meme_en_cas_erreur(
        self,
        scanner: AsusRouterScanner,
        mock_client: MagicMock,
        network_config: NetworkConfig,
    ) -> None:
        """logout() est appele meme si get_clients() leve une exception."""
        mock_client.get_clients.side_effect = RuntimeError(
            "Erreur reseau"
        )

        with pytest.raises(RuntimeError):
            scanner.scan(network_config)

        mock_client.logout.assert_called_once()
