"""Unit tests for configuration.py feature module."""

import pytest
from unittest.mock import patch, MagicMock


class TestConfigurationFeature:
    """Tests for ConfigurationFeature class."""

    def test_init(self):
        """Test ConfigurationFeature initialization."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        feature = ConfigurationFeature()

        assert feature.name == "Configuration"

    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_choice.return_value = "back"

        feature = ConfigurationFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    def test_execute_view_settings(self, mock_choice, mock_console):
        """Test execute view settings option."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_choice.side_effect = ["view", "back"]

        feature = ConfigurationFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    @patch("src.farmer_cli.features.configuration.text_prompt")
    def test_execute_edit_settings(self, mock_text, mock_choice, mock_console):
        """Test execute edit settings option."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_choice.side_effect = ["edit", "back"]
        mock_text.return_value = "new_value"

        feature = ConfigurationFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    @patch("src.farmer_cli.features.configuration.confirm_prompt")
    def test_execute_reset_settings(self, mock_confirm, mock_choice, mock_console):
        """Test execute reset settings option."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_choice.side_effect = ["reset", "back"]
        mock_confirm.return_value = True

        feature = ConfigurationFeature()
        feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        feature = ConfigurationFeature()
        # Should not raise
        feature.cleanup()
