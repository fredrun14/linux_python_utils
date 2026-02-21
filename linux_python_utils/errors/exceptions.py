"""
Module contenant les exceptions personnalisées pour flatpak_auto_update.

Ce module suit le principe SRP en isolant la gestion des exceptions.
"""
import os
from abc import ABC, abstractmethod

from dnf_configurator.exceptions import RollbackError


class ApplicationError(Exception):
    """Exception de base pour toutes les applications."""
    pass

class ConfigurationError(ApplicationError):
    """Exception de base pour toutes les Configurations."""
    pass

class FileConfigurationError(ConfigurationError):
    """ Exception de base pour toutes les fichiers de configurations    """
    pass

class SystemRequirementError(ApplicationError):
    """Exception de base pour toutes les systemes de dépendances."""
    pass

class MissingDependencyError(SystemRequirementError):
    """Exception de base pour toutes les dépendances manquantes."""
    pass

class ValidationError(ApplicationError):
    """Exception de base pour toutes les validations."""
    pass

class RollbackError(ApplicationError):
    """ Exception de base pour toutes les Rollback"""
    pass