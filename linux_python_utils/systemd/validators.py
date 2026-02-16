"""Fonctions de validation pour les noms d'unités systemd."""

import re


# Nom d'unité systemd : lettres, chiffres, points, tirets, underscores, ':'
_UNIT_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9:._-]*$')

# Nom de service : plus restrictif, pas de '.' ni ':'
_SERVICE_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')


def validate_unit_name(name: str) -> str:
    """Valide un nom d'unité systemd.

    Accepte les caractères : lettres, chiffres, points, tirets,
    underscores et deux-points. Le premier caractère doit être
    alphanumérique.

    Args:
        name: Nom d'unité à valider.

    Returns:
        Le nom validé.

    Raises:
        ValueError: Si le nom est invalide.
    """
    if not name:
        raise ValueError("Le nom d'unité ne peut pas être vide")
    if '..' in name or '/' in name:
        raise ValueError(
            f"Nom d'unité invalide (traversée interdite) : {name!r}"
        )
    if not _UNIT_NAME_RE.match(name):
        raise ValueError(
            f"Nom d'unité invalide : {name!r}"
        )
    return name


def validate_service_name(name: str) -> str:
    """Valide un nom de service systemd.

    Plus restrictif que validate_unit_name : rejette les points
    et les deux-points, ainsi que les séquences dangereuses.

    Args:
        name: Nom de service à valider.

    Returns:
        Le nom validé.

    Raises:
        ValueError: Si le nom est invalide.
    """
    if not name:
        raise ValueError("Le nom de service ne peut pas être vide")
    if '..' in name or '/' in name:
        raise ValueError(
            f"Nom de service invalide (traversée interdite) : "
            f"{name!r}"
        )
    if not _SERVICE_NAME_RE.match(name):
        raise ValueError(
            f"Nom de service invalide : {name!r}"
        )
    return name
