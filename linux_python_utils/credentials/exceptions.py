"""Exceptions pour le module credentials.

Ce module definit les exceptions metier levees lors
d'operations sur les credentials.
"""


class CredentialNotFoundError(Exception):
    """Levee quand un credential est absent de tous les providers."""


class CredentialStoreError(Exception):
    """Levee quand le stockage ou la suppression echoue."""


class CredentialProviderUnavailableError(Exception):
    """Levee quand un provider requis est indisponible."""
