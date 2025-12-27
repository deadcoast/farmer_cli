"""Tests for help_system.py module."""

from unittest.mock import MagicMock, patch

import pytest


class TestHelpSystem:
    """Tests for HelpSystem class."""

    def test_init(self):
        """Test HelpSystem initialization."""
        from src.farmer_cli.features.help_system import HelpSystem

        help_sys = HelpSystem()

        assert help_sys.name == "Help System"

    @patch("src.farmer_cli.features.help_system.display_full_help")
    def test_execute(self, mock_display):
        """Test execute method."""
        from src.farmer_cli.features.help_system import HelpSystem

        help_sys = HelpSystem()
        help_sys.execute()

        mock_display.assert_called_once()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.help_system import HelpSystem

        help_sys = HelpSystem()
        help_sys.cleanup()  # Should not raise


class TestDisplayFullHelp:
    """Tests for display_full_help function."""

    @patch("src.farmer_cli.features.help_system.console")
    def test_display_full_help(self, mock_console):
        """Test full help display."""
        from src.farmer_cli.features.help_system import display_full_help

        display_full_help()

        mock_console.clear.assert_called_once()
        mock_console.print.assert_called()
        mock_console.input.assert_called_once()


class TestDisplayQuickHelp:
    """Tests for display_quick_help function."""

    @patch("src.farmer_cli.features.help_system.console")
    def test_display_quick_help(self, mock_console):
        """Test quick help display."""
        from src.farmer_cli.features.help_system import display_quick_help

        display_quick_help()

        mock_console.clear.assert_called_once()
        mock_console.print.assert_called()


class TestSearchableHelp:
    """Tests for searchable_help function."""

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.text_prompt")
    def test_searchable_help_found(self, mock_prompt, mock_console):
        """Test searchable help with results found."""
        from src.farmer_cli.features.help_system import searchable_help

        mock_prompt.return_value = "theme"

        searchable_help()

        mock_console.clear.assert_called_once()
        assert mock_console.print.call_count >= 2

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.text_prompt")
    def test_searchable_help_not_found(self, mock_prompt, mock_console):
        """Test searchable help with no results."""
        from src.farmer_cli.features.help_system import searchable_help

        mock_prompt.return_value = "xyznonexistent"

        searchable_help()

        mock_console.clear.assert_called_once()
        mock_console.print.assert_called()


class TestHelpContent:
    """Tests for HELP_CONTENT dictionary."""

    def test_help_content_exists(self):
        """Test that help content dictionary exists."""
        from src.farmer_cli.features.help_system import HELP_CONTENT

        assert isinstance(HELP_CONTENT, dict)
        assert len(HELP_CONTENT) > 0

    def test_help_content_has_overview(self):
        """Test that help content has overview."""
        from src.farmer_cli.features.help_system import HELP_CONTENT

        assert "overview" in HELP_CONTENT
