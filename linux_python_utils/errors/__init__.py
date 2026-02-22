"""Module de gestion des errors."""

from linux_python_utils.errors.base import ErrorHandler, ErrorHandlerChain
from linux_python_utils.errors.exceptions import (ApplicationError,
                                                  ConfigurationError,
                                                  FileConfigurationError,
                                                  SystemRequirementError,
                                                  MissingDependencyError,
                                                  ValidationError,
                                                  InstallationError,
                                                  AppPermissionError,
                                                  RollbackError,
                                                  IntegrityError)
from linux_python_utils.errors.console_handler import ConsoleErrorHandler
from linux_python_utils.errors.logger_handler import LoggerErrorHandler
from linux_python_utils.errors.context import ErrorContext


__all__ = [
    "ApplicationError",
    "ConfigurationError",
    "FileConfigurationError",
    "SystemRequirementError",
    "MissingDependencyError",
    "ValidationError",
    "InstallationError",
    "AppPermissionError",
    "RollbackError",
    "IntegrityError",
    "ErrorHandler",
    "ConsoleErrorHandler",
    "LoggerErrorHandler",
    "ErrorHandlerChain",
    "ErrorContext",
]