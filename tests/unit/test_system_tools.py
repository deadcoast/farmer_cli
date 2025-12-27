"""Unit tests for system_tools.py feature module."""

import pytest
from unittest.mock import patch, MagicMock


class TestSystemToolsFeature:
    """Tests for SystemToolsFeature class."""

    def test_init(self):
        """Test SystemToolsFeature initialization."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()

        assert feature.name == "System Tools"

    @patch("src.farmer_cli.features.system_tools.console")
    @patch("src.farmer_cli.features.system_tools.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        mock_choice.return_value = "back"

        feature = SystemToolsFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.system_tools.console")
    @patch("src.farmer_cli.features.system_tools.choice_prompt")
    def test_execute_system_info(self, mock_choice, mock_console):
        """Test execute system info option."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        mock_choice.side_effect = ["info", "back"]

        feature = SystemToolsFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.system_tools.console")
    @patch("src.farmer_cli.features.system_tools.choice_prompt")
    def test_execute_disk_usage(self, mock_choice, mock_console):
        """Test execute disk usage option."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        mock_choice.side_effect = ["disk", "back"]

        feature = SystemToolsFeature()
        feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        # Should not raise
        feature.cleanup()
