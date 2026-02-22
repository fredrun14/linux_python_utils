"""Modeles de donnees pour la gestion des credentials.

Ce module definit les dataclasses immuables CredentialKey
et Credential representant les cles et valeurs de secrets
applicatifs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CredentialKey:
    """Cle d'identification d'un credential.

    Attributes:
        service: Nom du service applicatif (ex: "scannethome").
        key: Nom de la cle (ex: "ASUS_ROUTER_PASSWORD").
    """

    service: str
    key: str

    def __post_init__(self) -> None:
        """Valide les champs apres initialisation."""
        if not self.service or not self.service.strip():
            raise ValueError(
                "Le champ 'service' ne peut pas etre vide."
            )
        if not self.key or not self.key.strip():
            raise ValueError(
                "Le champ 'key' ne peut pas etre vide."
            )


@dataclass(frozen=True)
class Credential:
    """Credential complet : service, cle et valeur.

    Attributes:
        service: Nom du service applicatif.
        key: Nom de la cle.
        value: Valeur secrete du credential.
        source: Source d'ou provient la valeur
            (ex: "env", "dotenv", "keyring").
    """

    service: str
    key: str
    value: str
    source: str = ""

    def __post_init__(self) -> None:
        """Valide les champs apres initialisation."""
        if not self.service or not self.service.strip():
            raise ValueError(
                "Le champ 'service' ne peut pas etre vide."
            )
        if not self.key or not self.key.strip():
            raise ValueError(
                "Le champ 'key' ne peut pas etre vide."
            )

    @property
    def credential_key(self) -> CredentialKey:
        """Retourne la cle d'identification du credential.

        Returns:
            Instance de CredentialKey.
        """
        return CredentialKey(
            service=self.service,
            key=self.key,
        )
