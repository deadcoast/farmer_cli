"""Unit tests for help_system.py feature module."""

import pytest
from unittest.mock import patch, MagicMock


class TestHelpSystemFeature:
    """Tests for HelpSystemFeature class."""

    def test_init(self):
        """Test HelpSystemFeature initialization."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        feature = HelpSystemFeature()

        assert feature.name == "Help System"

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        mock_choice.return_value = "back"

        feature = HelpSystemFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.choice_prompt")
    def test_execute_show_help(self, mock_choice, mock_console):
        """Test execute show help option."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        mock_choice.side_effect = ["general", "back"]

        feature = HelpSystemFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.choice_prompt")
    def test_execute_show_commands(self, mock_choice, mock_console):
        """Test execute show commands option."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        mock_choice.side_effect = ["commands", "back"]

        feature = HelpSystemFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.help_system.console")
    @patch("src.farmer_cli.features.help_system.choice_prompt")
    def test_execute_show_about(self, mock_choice, mock_console):
        """Test execute show about option."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        mock_choice.side_effect = ["about", "back"]

        feature = HelpSystemFeature()
        feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.help_system import HelpSystemFeature

        feature = HelpSystemFeature()
        # Should not raise
        feature.cleanup()


class TestGetHelpContent:
    """Tests for get_help_content function."""

    def test_get_help_content_general(self):
        """Test getting general help content."""
        from src.farmer_cli.features.help_system import get_help_content

        result = get_help_content("general")

        assert result is not None
        assert isinstance(result, str)

    def test_get_help_content_commands(self):
        """Test getting commands help content."""
        from src.farmer_cli.features.help_system import get_help_content

        result = get_help_content("commands")

        assert result is not None

    def test_get_help_content_unknown(self):
        """Test getting unknown help topic."""
        from src.farmer_cli.features.help_system import get_help_content

        result = get_help_content("unknown_topic")

        # Should return default or empty content
        assert result is not None or result == ""
