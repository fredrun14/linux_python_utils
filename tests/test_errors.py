#!/usr/bin/env python3
"""Tests unitaires pour le module errors."""

import unittest
from unittest.mock import MagicMock, patch


from linux_python_utils.errors.base import ErrorHandler, ErrorHandlerChain
from linux_python_utils.errors.exceptions import (ApplicationError,
                                                  ConfigurationError,
                                                  FileConfigurationError,
                                                  SystemRequirementError,
                                                  MissingDependencyError,
                                                  ValidationError,
                                                  InstallationError,
                                                  AppPermissionError,
                                                  RollbackError)
from linux_python_utils.errors.console_handler import ConsoleErrorHandler
from linux_python_utils.errors.logger_handler import LoggerErrorHandler
from linux_python_utils.errors.context import ErrorContext



class TestConsoleErrorHandler(unittest.TestCase):
    """Tests pour ConsoleErrorHandler."""

    def setUp(self):
        self.handler = ConsoleErrorHandler()

    @patch("builtins.print")
    def test_handle_missing_dependency(self, mock_print):
        """Vérifie le message pour MissingDependencyError."""
        error = MissingDependencyError("flatpak manquant")
        self.handler.handle(error)
        mock_print.assert_any_call("\n🛑 MissingDependencyError: flatpak manquant")
        mock_print.assert_any_call(
            "\n🔧 Solution : Installez les dépendances manquantes comme indiqué."
        )

    @patch("builtins.print")
    def test_handle_permission_error(self, mock_print):
        """Vérifie le message pour AppPermissionError."""
        error = AppPermissionError("permission refusée")
        self.handler.handle(error)
        mock_print.assert_any_call(
            "\n🔧 Solution : Exécutez avec sudo ou vérifiez les permissions."
        )

    @patch("builtins.print")
    def test_handle_configuration_error(self, mock_print):
        """Vérifie le message pour ConfigurationError."""
        error = ConfigurationError("config invalide")
        self.handler.handle(error)
        mock_print.assert_any_call(
            "\n🔧 Solution : Vérifiez votre fichier de configuration."
        )

    @patch("builtins.print")
    def test_handle_installation_error(self, mock_print):
        """Vérifie le message pour InstallationError."""
        error = InstallationError("install échouée")
        self.handler.handle(error)
        mock_print.assert_any_call(
            "\n🔧 Solution : Consultez les logs pour plus de détails."
        )

    @patch("builtins.print")
    def test_handle_generic_flatpak_error(self, mock_print):
        """Vérifie le message par défaut pour ValidationError."""
        error = ValidationError("validation échouée")
        self.handler.handle(error)
        mock_print.assert_any_call("\n🔧 Solution : Voir les suggestions ci-dessus.")

    @patch("builtins.print")
    def test_handle_subclass_matches_parent(self, mock_print):
        """FileConfigurationError hérite de ConfigurationError, doit matcher."""
        error = FileConfigurationError("fichier invalide")
        self.handler.handle(error)
        mock_print.assert_any_call(
            "\n🔧 Solution : Vérifiez votre fichier de configuration."
        )

    @patch("builtins.print")
    def test_handle_unknown_error(self, mock_print):
        """Vérifie le message pour une erreur inconnue."""
        error = RuntimeError("erreur inconnue")
        self.handler.handle(error)
        mock_print.assert_any_call("\n💥 Erreur inattendue: erreur inconnue")
        mock_print.assert_any_call("Type: RuntimeError")


class TestLoggerErrorHandler(unittest.TestCase):
    """Tests pour LoggerErrorHandler."""

    def setUp(self):
        self.mock_logger = MagicMock()
        self.handler = LoggerErrorHandler(self.mock_logger)

    def test_handle_known_error(self):
        """Vérifie le log pour une erreur connue."""
        error = ConfigurationError("config invalide")
        self.handler.handle(error)
        self.mock_logger.log_error.assert_called_once_with(
            "ConfigurationError: config invalide"
        )

    def test_handle_unknown_error(self):
        """Vérifie le log pour une erreur inconnue."""
        error = RuntimeError("runtime error")
        self.handler.handle(error)
        self.mock_logger.log_error.assert_called_once_with(
            "Erreur inattendue: RuntimeError: runtime error"
        )


class TestErrorHandlerChain(unittest.TestCase):
    """Tests pour ErrorHandlerChain."""

    def test_handle_calls_all_handlers(self):
        """Vérifie que tous les handlers sont appelés."""
        chain = ErrorHandlerChain()
        handler1 = MagicMock()
        handler2 = MagicMock()
        chain.add_handler(handler1)
        chain.add_handler(handler2)

        error = RuntimeError("test")
        chain.handle(error)

        handler1.handle.assert_called_once_with(error)
        handler2.handle.assert_called_once_with(error)

    def test_handle_and_exit(self):
        """Vérifie que handle_and_exit appelle sys.exit."""
        chain = ErrorHandlerChain()
        handler = MagicMock()
        chain.add_handler(handler)

        error = RuntimeError("test")
        with self.assertRaises(SystemExit) as ctx:
            chain.handle_and_exit(error, exit_code=2)

        self.assertEqual(ctx.exception.code, 2)
        handler.handle.assert_called_once_with(error)


class TestErrorContext(unittest.TestCase):
    """Tests pour ErrorContext."""

    def setUp(self):
        self.mock_logger = MagicMock()
        self.context = ErrorContext(self.mock_logger)

    def test_add_rollback_action(self):
        """Vérifie l'ajout d'une action de rollback."""
        action = MagicMock()
        self.context.add_rollback_action(action, "test action")
        self.assertEqual(len(self.context.rollback_actions), 1)

    def test_execute_rollback_success(self):
        """Vérifie l'exécution réussie du rollback."""
        action = MagicMock()
        self.context.add_rollback_action(action, "action test")

        self.context.execute_rollback()

        action.assert_called_once()
        self.mock_logger.log_info.assert_any_call("Rollback réussi: action test")

    def test_execute_rollback_reversed_order(self):
        """Vérifie que les actions sont exécutées en ordre inverse."""
        call_order = []
        self.context.add_rollback_action(lambda: call_order.append(1), "action 1")
        self.context.add_rollback_action(lambda: call_order.append(2), "action 2")

        self.context.execute_rollback()

        self.assertEqual(call_order, [2, 1])

    def test_execute_rollback_raises_on_failure(self):
        """Vérifie que RollbackError est levé en cas d'échec."""
        action = MagicMock(side_effect=RuntimeError("rollback failed"))
        self.context.add_rollback_action(action, "failing action")

        with self.assertRaises(RollbackError):
            self.context.execute_rollback()

    def test_execute_rollback_continues_after_failure(self):
        """Vérifie que toutes les actions sont tentées malgré un échec."""
        action1 = MagicMock(side_effect=RuntimeError("fail"))
        action2 = MagicMock()
        self.context.add_rollback_action(action1, "failing")
        self.context.add_rollback_action(action2, "succeeding")

        with self.assertRaises(RollbackError):
            self.context.execute_rollback()

        # Les deux actions doivent avoir été appelées (ordre inversé)
        action1.assert_called_once()
        action2.assert_called_once()

    def test_handle_error_with_rollback(self):
        """Vérifie handle_error_with_rollback exécute le rollback."""
        action = MagicMock()
        self.context.add_rollback_action(action, "rollback action")

        error = ConfigurationError("test error")
        self.context.handle_error_with_rollback(error)

        action.assert_called_once()

    def test_handle_error_with_rollback_catches_rollback_error(self):
        """Vérifie que RollbackError ne se propage pas hors de handle_error_with_rollback."""
        action = MagicMock(side_effect=RuntimeError("fail"))
        self.context.add_rollback_action(action, "failing action")

        error = ConfigurationError("test error")
        # Ne doit pas lever RollbackError
        self.context.handle_error_with_rollback(error)

    def test_handle_error_without_rollback_actions(self):
        """Vérifie le comportement sans actions de rollback."""
        error = ConfigurationError("test error")
        self.context.handle_error_with_rollback(error)

        self.mock_logger.log_info.assert_called_with(
            "Aucune action de rollback nécessaire."
        )

    def test_clear_rollback_actions(self):
        """Vérifie la suppression de toutes les actions."""
        self.context.add_rollback_action(MagicMock(), "action")
        self.context.clear_rollback_actions()
        self.assertEqual(len(self.context.rollback_actions), 0)


if __name__ == '__main__':
    unittest.main()
