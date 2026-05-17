"""Tests pour linux_python_utils.identity.group."""

from unittest.mock import MagicMock, patch

import pytest

from linux_python_utils.commands import LinuxCommandExecutor
from linux_python_utils.identity.group import LinuxGroupManager
from linux_python_utils.logging.base import Logger


@pytest.fixture
def executor() -> MagicMock:
    return MagicMock(spec=LinuxCommandExecutor)


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def manager(executor: MagicMock, logger: MagicMock) -> LinuxGroupManager:
    return LinuxGroupManager(executor, logger)


class TestLinuxGroupManagerEnsureGroup:
    """Tests pour LinuxGroupManager.ensure_group."""

    def test_ensure_group_correct_gid_skips(
        self,
        manager: LinuxGroupManager,
        executor: MagicMock,
    ) -> None:
        """GID correct → aucun appel executor."""
        # Arrange
        mock_grp = MagicMock()
        mock_grp.gr_gid = 1042

        # Act
        with patch(
            "linux_python_utils.identity.group.grp.getgrnam",
            return_value=mock_grp,
        ):
            manager.ensure_group("partage-lan", 1042)

        # Assert
        executor.run.assert_not_called()

    def test_ensure_group_wrong_gid_calls_groupmod(
        self,
        manager: LinuxGroupManager,
        executor: MagicMock,
    ) -> None:
        """GID incorrect → groupmod --gid."""
        # Arrange
        mock_grp = MagicMock()
        mock_grp.gr_gid = 9999

        # Act
        with patch(
            "linux_python_utils.identity.group.grp.getgrnam",
            return_value=mock_grp,
        ):
            manager.ensure_group("partage-lan", 1042)

        # Assert
        executor.run.assert_called_once()
        cmd = executor.run.call_args[0][0]
        assert cmd[0] == "groupmod"
        assert "--gid" in cmd
        assert "1042" in cmd
        assert "partage-lan" in cmd

    def test_ensure_group_missing_calls_groupadd(
        self,
        manager: LinuxGroupManager,
        executor: MagicMock,
    ) -> None:
        """Groupe absent → groupadd --gid."""
        # Act
        with patch(
            "linux_python_utils.identity.group.grp.getgrnam",
            side_effect=KeyError("partage-lan"),
        ):
            manager.ensure_group("partage-lan", 1042)

        # Assert
        executor.run.assert_called_once()
        cmd = executor.run.call_args[0][0]
        assert cmd[0] == "groupadd"
        assert "--gid" in cmd
        assert "1042" in cmd
        assert "partage-lan" in cmd
