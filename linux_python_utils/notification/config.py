"""Configuration pour les notifications desktop Linux.

Ce module fournit une dataclass pour configurer les notifications
envoyées via notify-send sur les systèmes Linux avec KDE Plasma
ou d'autres environnements de bureau compatibles.

Example:
    Création d'une configuration de notification:

        config = NotificationConfig(
            title="Mise à jour",
            message_success="Mise à jour réussie.",
            message_failure="Échec de la mise à jour."
        )
        bash_function = config.to_bash_function()
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationConfig:
    """Configuration pour les notifications desktop Linux.

    Cette dataclass encapsule tous les paramètres nécessaires pour
    envoyer des notifications via notify-send à tous les utilisateurs
    connectés sur un système Linux.

    Attributes:
        title: Titre de la notification.
        message_success: Message affiché en cas de succès.
        message_failure: Message affiché en cas d'échec.
        icon_success: Icône affichée en cas de succès.
        icon_failure: Icône affichée en cas d'échec.

    Example:
        >>> config = NotificationConfig(
        ...     title="Flatpak Update",
        ...     message_success="Mise à jour terminée.",
        ...     message_failure="Échec de la mise à jour."
        ... )
        >>> print(config.title)
        Flatpak Update
    """

    title: str
    message_success: str
    message_failure: str
    icon_success: str = "software-update-available"
    icon_failure: str = "dialog-error"

    def __post_init__(self) -> None:
        """Valide les champs requis après initialisation.

        Raises:
            ValueError: Si un champ requis est vide.
        """
        if not self.title:
            raise ValueError("title est requis")
        if not self.message_success:
            raise ValueError("message_success est requis")
        if not self.message_failure:
            raise ValueError("message_failure est requis")

    def to_bash_function(self) -> str:
        """Génère la fonction bash send_notification().

        Cette fonction bash envoie une notification à tous les
        utilisateurs connectés via notify-send en utilisant leur
        session D-Bus respective.

        Returns:
            Code bash de la fonction send_notification().

        Example:
            >>> config = NotificationConfig(
            ...     title="Update",
            ...     message_success="OK",
            ...     message_failure="Erreur"
            ... )
            >>> bash_code = config.to_bash_function()
            >>> "send_notification()" in bash_code
            True
        """
        return '''send_notification() {
    local title="$1"
    local message="$2"
    local icon="$3"

    # Envoyer la notification à tous les utilisateurs connectés
    for user_id in $(loginctl list-users --no-legend \\
        | awk '{print $1}'); do
        user_name=$(loginctl list-users --no-legend \\
            | awk -v id="$user_id" '$1==id {print $2}')
        user_runtime_dir="/run/user/$user_id"

        if [ -S "$user_runtime_dir/bus" ]; then
            # Exécuter notify-send avec timeout en arrière-plan
            timeout 10 runuser -u "$user_name" -- env \\
                DBUS_SESSION_BUS_ADDRESS="unix:path=$user_runtime_dir/bus" \\
                notify-send -i "$icon" -a "Flatpak" "$title" "$message" &
        fi
    done
    # Attendre brièvement que les notifications soient envoyées
    sleep 1
}'''

    def to_bash_call_success(self) -> str:
        """Génère l'appel bash pour une notification de succès.

        Returns:
            Ligne bash appelant send_notification avec paramètres succès.
        """
        return (
            f'send_notification "{self.title}" '
            f'"{self.message_success}" "{self.icon_success}"'
        )

    def to_bash_call_failure(self) -> str:
        """Génère l'appel bash pour une notification d'échec.

        Returns:
            Ligne bash appelant send_notification avec paramètres échec.
        """
        return (
            f'send_notification "{self.title}" '
            f'"{self.message_failure}" "{self.icon_failure}"'
        )
