"""
    LoggerErrorHandler
"""
from linux_python_utils.errors.base import ErrorHandler
from linux_python_utils.errors.exceptions import ApplicationError

from linux_python_utils import Logger


class LoggerErrorHandler(ErrorHandler):
    """Handler pour logger les erreurs.

    Enregistre les erreurs dans le fichier de log via le Logger
    injecté au constructeur.
    """

    def __init__(self,
                 logger: Logger,
                 base_error_type: type[Exception] = ApplicationError
                 ) -> None:
        """Initialise le handler avec un logger.

        Args:
            logger: Instance de Logger pour l'enregistrement des erreurs.
        """
        self.logger = logger

    def handle(self, error: Exception) -> None:
        """Log l'erreur avec différents niveaux selon la gravité.

        Args:
            error: L'exception à logger.
        """
        if isinstance(error, ApplicationError):
            self.logger.log_error(f"{type(error).__name__}: {str(error)}")
        else:
            self.logger.log_error(
                f"Erreur inattendue: {type(error).__name__}: {str(error)}"
            )
