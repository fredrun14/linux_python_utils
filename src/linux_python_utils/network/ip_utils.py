"""Utilitaires de conversion IPv4 et allocation DHCP."""

import ipaddress
from typing import Iterator, Optional, Set

from linux_python_utils.network.config import DhcpRange


def _ip_to_int(ip: str) -> int:
    """Convertit une adresse IPv4 en entier.

    Args:
        ip: Adresse IPv4 au format a.b.c.d.

    Returns:
        Representation entiere.

    Raises:
        ValueError: Si ip n'est pas une adresse IPv4 valide.
    """
    try:
        return int(ipaddress.IPv4Address(ip))
    except ipaddress.AddressValueError as exc:
        raise ValueError(
            f"Adresse IPv4 invalide : {ip!r}"
        ) from exc


def _int_to_ip(num: int) -> str:
    """Convertit un entier en adresse IPv4.

    Args:
        num: Representation entiere.

    Returns:
        Adresse IPv4 au format a.b.c.d.
    """
    return str(ipaddress.IPv4Address(num))


def _iter_free_ips(
    start: str, end: str, used_ips: Set[str]
) -> Iterator[str]:
    """Itere sur les IP libres dans la plage [start, end].

    Args:
        start: Premiere adresse de la plage.
        end: Derniere adresse de la plage.
        used_ips: Ensemble des IP deja utilisees.

    Yields:
        Prochaine IP libre.
    """
    start_int = _ip_to_int(start)
    end_int = _ip_to_int(end)
    for num in range(start_int, end_int + 1):
        ip = _int_to_ip(num)
        if ip not in used_ips:
            yield ip


def _next_available_ip(
    dhcp_range: DhcpRange, used_ips: Set[str]
) -> Optional[str]:
    """Retourne la premiere IP libre dans la plage ou None.

    Args:
        dhcp_range: Plage DHCP.
        used_ips: Ensemble des IP deja utilisees.

    Returns:
        Prochaine IP disponible ou None si plage epuisee.
    """
    return next(
        _iter_free_ips(
            dhcp_range.start, dhcp_range.end, used_ips
        ),
        None,
    )
