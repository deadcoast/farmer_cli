"""Tests for data_processing.py module."""

from unittest.mock import MagicMock, patch

import pytest


class TestDataProcessingFeature:
    """Tests for DataProcessingFeature class."""

    def test_init(self):
        """Test DataProcessingFeature initialization."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()

        assert feature.name == "Data Processing"
        assert feature.description == "Advanced data processing and analysis tools"
        assert feature.menu_manager is not None

    @patch("src.farmer_cli.features.data_processing.MenuManager")
    def test_execute_exit(self, mock_menu_class):
        """Test execute with exit choice."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.return_value = None
        mock_menu_class.return_value = mock_menu

        feature = DataProcessingFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_menu.display_submenu.assert_called_once()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.MenuManager")
    def test_execute_code_snippet(self, mock_menu_class, mock_console):
        """Test execute with code snippet choice."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["1", None]
        mock_menu_class.return_value = mock_menu

        feature = DataProcessingFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()
        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.MenuManager")
    def test_execute_system_info(self, mock_menu_class, mock_console):
        """Test execute with system info choice."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["2", None]
        mock_menu_class.return_value = mock_menu

        feature = DataProcessingFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.create_table")
    @patch("src.farmer_cli.features.data_processing.MenuManager")
    def test_execute_sample_table(self, mock_menu_class, mock_table, mock_console):
        """Test execute with sample table choice."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["3", None]
        mock_menu_class.return_value = mock_menu
        mock_table.return_value = MagicMock()

        feature = DataProcessingFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()
        mock_table.assert_called_once()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.show_progress")
    @patch("src.farmer_cli.features.data_processing.sleep")
    @patch("src.farmer_cli.features.data_processing.MenuManager")
    def test_execute_progress_simulation(self, mock_menu_class, mock_sleep, mock_progress, mock_console):
        """Test execute with progress simulation choice."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["4", None]
        mock_menu_class.return_value = mock_menu

        # Mock progress context manager
        mock_progress_ctx = MagicMock()
        mock_task = MagicMock()
        mock_progress_ctx.add_task.return_value = mock_task
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_ctx)
        mock_progress.return_value.__exit__ = MagicMock(return_value=False)

        feature = DataProcessingFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()
        # Should not raise
        feature.cleanup()


class TestDisplayCodeSnippet:
    """Tests for _display_code_snippet method."""

    @patch("src.farmer_cli.features.data_processing.console")
    def test_display_code_snippet(self, mock_console):
        """Test code snippet display."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()
        feature._display_code_snippet()

        mock_console.clear.assert_called_once()
        # Should print the code snippet
        assert mock_console.print.call_count >= 2


class TestShowSystemInfo:
    """Tests for _show_system_info method."""

    @patch("src.farmer_cli.features.data_processing.console")
    def test_show_system_info(self, mock_console):
        """Test system info display."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()
        feature._show_system_info()

        mock_console.clear.assert_called_once()
        mock_console.print.assert_called()


class TestDisplaySampleTable:
    """Tests for _display_sample_table method."""

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.create_table")
    def test_display_sample_table(self, mock_table, mock_console):
        """Test sample table display."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_table.return_value = MagicMock()

        feature = DataProcessingFeature()
        feature._display_sample_table()

        mock_console.clear.assert_called_once()
        mock_table.assert_called_once()


class TestSimulateProgress:
    """Tests for _simulate_progress method."""

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.show_progress")
    @patch("src.farmer_cli.features.data_processing.sleep")
    def test_simulate_progress(self, mock_sleep, mock_progress, mock_console):
        """Test progress simulation."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        # Mock progress context manager
        mock_progress_ctx = MagicMock()
        mock_task = MagicMock()
        mock_progress_ctx.add_task.return_value = mock_task
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_ctx)
        mock_progress.return_value.__exit__ = MagicMock(return_value=False)

        feature = DataProcessingFeature()
        feature._simulate_progress()

        mock_console.clear.assert_called_once()
        mock_progress.assert_called_once()
