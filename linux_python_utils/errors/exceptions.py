"""
Module contenant les exceptions communes.

Ce module suit le principe SRP en isolant la gestion des exceptions.
"""

class ApplicationError(Exception):
    """Exception de base pour toutes les applications."""
    pass

class ConfigurationError(ApplicationError):
    """Exception de base pour toutes les Configurations."""
    pass

class FileConfigurationError(ConfigurationError):
    """ Exception de base pour tous les fichiers de configurations    """
    pass

class SystemRequirementError(ApplicationError):
    """Exception de base pour tous les systèmes de dépendances."""
    pass

class MissingDependencyError(SystemRequirementError):
    """Exception de base pour toutes les dépendances manquantes."""
    pass

class ValidationError(ApplicationError):
    """Exception de base pour toutes les validations."""
    pass

class InstallationError(ApplicationError):
    """Exception de base pour toutes les installations."""
    pass

class AppPermissionError(ApplicationError):
    """Exception de base pour toutes les permissions applicatives."""
    pass

class RollbackError(ApplicationError):
    """ Exception de base pour toutes les Rollback"""
    pass