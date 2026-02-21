"""

"""
from linux_python_utils.errors.base import ErrorHandler
from linux_python_utils.errors.exceptions import ApplicationError

from flatpak_auto_update.exceptions import (
    ConfigurationError,
    InstallationError,
    MissingDependencyError,
    RollbackError,
)

class ConsoleErrorHandler(ErrorHandler):
    """Handler pour afficher les erreurs dans la console.

    Distingue les erreurs connues (FlatpakAutoUpdateError)
    des erreurs inattendues, et affiche un message de solution
    adapté au type d'erreur.
    """

    def __init__(
        self,
        base_error_type: type[Exception] = ApplicationError,
        solutions: dict[type[Exception],str] | None = None
    ) -> None:
        """  ConsoleErrorHandler (générique, configurable)

            Attributes:
                base_error_type : classe de base pour distinguer erreurs connues/inconnues
                                   (défaut: ApplicationError)
                solutions : dictionnaire {TypeException: "message solution"}
                    Les projets passent leurs propres mappings à l'instanciation.
        """

    def handle(self, error: Exception) -> None:
        """Affiche l'erreur dans la console avec des messages utilisateur.

        Args:
            error: L'exception à afficher.
        """
        if isinstance(error, ApplicationError):
            self._handle_known_error(error)
        else:
            self._handle_unknown_error(error)

    def _handle_known_error(self, error: ApplicationError) -> None:
        """Gère les erreurs connues du projet.

        Affiche le type et le message de l'erreur, suivi d'une
        suggestion de solution adaptée via isinstance.

        Args:
            error: L'exception métier à traiter.
        """
        print(f"\n🛑 {type(error).__name__}: {str(error)}")

        if isinstance(error, MissingDependencyError):
            print("\n🔧 Solution : Installez les dépendances manquantes comme indiqué.")
        elif isinstance(error, ConfigurationError):
            print("\n🔧 Solution : Vérifiez votre fichier de configuration.")
        elif isinstance(error, InstallationError):
            print("\n🔧 Solution : Consultez les logs pour plus de détails.")
        else:
            print("\n🔧 Solution : Voir les suggestions ci-dessus.")

    def _handle_unknown_error(self, error: Exception) -> None:
        """Gère les erreurs inattendues.

        Args:
            error: L'exception non prévue à afficher.
        """
        print(f"\n💥 Erreur inattendue: {str(error)}")
        print(f"Type: {type(error).__name__}")
        print(
            "\n📋 Cela peut être un bug. Veuillez ouvrir une issue avec ces informations."
        )