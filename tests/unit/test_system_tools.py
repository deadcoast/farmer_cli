"""Tests for system_tools.py module."""

from unittest.mock import MagicMock, patch

import pytest


class TestSystemToolsFeature:
    """Tests for SystemToolsFeature class."""

    def test_init(self):
        """Test SystemToolsFeature initialization."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()

        assert feature.name == "System Tools"
        assert feature.menu_manager is not None

    def test_execute_exit(self):
        """Test execute with exit choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.return_value = None

        feature.execute()

        feature.menu_manager.display_submenu.assert_called_once()

    @patch("src.farmer_cli.features.system_tools.browse_files")
    def test_execute_browse_files(self, mock_browse):
        """Test execute with browse files choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.side_effect = ["1", None]

        feature.execute()

        mock_browse.assert_called_once()

    @patch("src.farmer_cli.features.system_tools.check_weather")
    def test_execute_check_weather(self, mock_weather):
        """Test execute with check weather choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.side_effect = ["2", None]

        feature.execute()

        mock_weather.assert_called_once()

    @patch("src.farmer_cli.features.system_tools.export_help_to_pdf")
    def test_execute_export_pdf(self, mock_export):
        """Test execute with export PDF choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.side_effect = ["3", None]

        feature.execute()

        mock_export.assert_called_once()

    @patch("src.farmer_cli.features.system_tools.submit_feedback")
    def test_execute_submit_feedback(self, mock_feedback):
        """Test execute with submit feedback choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.side_effect = ["4", None]

        feature.execute()

        mock_feedback.assert_called_once()

    def test_execute_log_viewer(self):
        """Test execute with log viewer choice."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.menu_manager = MagicMock()
        feature.menu_manager.display_submenu.side_effect = ["5", None]
        feature.log_viewer = MagicMock()

        feature.execute()

        feature.log_viewer.execute.assert_called_once()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature.cleanup()  # Should not raise


class TestExportHelp:
    """Tests for _export_help method."""

    @patch("src.farmer_cli.features.system_tools.console")
    @patch("src.farmer_cli.features.system_tools.export_help_to_pdf")
    def test_export_help_success(self, mock_export, mock_console):
        """Test successful help export."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        feature = SystemToolsFeature()
        feature._export_help()

        mock_export.assert_called_once()
        mock_console.input.assert_called_once()

    @patch("src.farmer_cli.features.system_tools.console")
    @patch("src.farmer_cli.features.system_tools.export_help_to_pdf")
    def test_export_help_error(self, mock_export, mock_console):
        """Test help export with error."""
        from src.farmer_cli.features.system_tools import SystemToolsFeature

        mock_export.side_effect = Exception("Export failed")

        feature = SystemToolsFeature()
        feature._export_help()

        mock_console.print.assert_called()
        mock_console.input.assert_called()
