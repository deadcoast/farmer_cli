"""Tests for configuration.py feature module."""

from unittest.mock import MagicMock, patch

import pytest


class TestConfigurationFeature:
    """Tests for ConfigurationFeature class."""

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    def test_init(self):
        """Test ConfigurationFeature initialization."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        feature = ConfigurationFeature()

        assert feature.name == "Configuration"
        assert feature.app is None

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    def test_init_with_app(self):
        """Test ConfigurationFeature initialization with app."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_app = MagicMock()
        feature = ConfigurationFeature(app=mock_app)

        assert feature.app == mock_app

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    @patch("src.farmer_cli.features.configuration.MenuManager")
    def test_execute_exit(self, mock_menu_class):
        """Test execute with exit choice."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.return_value = None
        mock_menu_class.return_value = mock_menu

        feature = ConfigurationFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_menu.display_submenu.assert_called_once()


    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default", "description": "Default theme"}})
    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    @patch("src.farmer_cli.features.configuration.sleep")
    @patch("src.farmer_cli.features.configuration.MenuManager")
    def test_execute_select_theme(self, mock_menu_class, mock_sleep, mock_choice, mock_console):
        """Test execute with select theme choice."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["1", None]
        mock_menu_class.return_value = mock_menu
        mock_choice.return_value = "1"

        feature = ConfigurationFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.MenuManager")
    def test_execute_display_time(self, mock_menu_class, mock_console):
        """Test execute with display time choice."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["3", None]
        mock_menu_class.return_value = mock_menu

        feature = ConfigurationFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    @patch("src.farmer_cli.features.configuration.searchable_help")
    @patch("src.farmer_cli.features.configuration.MenuManager")
    def test_execute_help_search(self, mock_menu_class, mock_help):
        """Test execute with help search choice."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_menu = MagicMock()
        mock_menu.display_submenu.side_effect = ["4", None]
        mock_menu_class.return_value = mock_menu

        feature = ConfigurationFeature()
        feature.menu_manager = mock_menu
        feature.execute()

        mock_help.assert_called_once()

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        feature = ConfigurationFeature()
        # Should not raise
        feature.cleanup()


class TestSelectTheme:
    """Tests for _select_theme method."""

    @patch("src.farmer_cli.features.configuration.THEMES", {"dark": {"name": "Dark", "description": "Dark theme"}})
    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    @patch("src.farmer_cli.features.configuration.sleep")
    def test_select_theme_with_app(self, mock_sleep, mock_choice, mock_console):
        """Test theme selection with app reference."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_app = MagicMock()
        mock_choice.return_value = "1"

        feature = ConfigurationFeature(app=mock_app)
        feature._select_theme()

        mock_app.change_theme.assert_called_once_with("dark")

    @patch("src.farmer_cli.features.configuration.THEMES", {"light": {"name": "Light"}})
    @patch("src.farmer_cli.features.configuration.console")
    @patch("src.farmer_cli.features.configuration.choice_prompt")
    @patch("src.farmer_cli.features.configuration.sleep")
    def test_select_theme_without_app(self, mock_sleep, mock_choice, mock_console):
        """Test theme selection without app reference."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_choice.return_value = "1"

        feature = ConfigurationFeature()
        feature._select_theme()

        # Should not raise even without app
        mock_console.print.assert_called()


class TestDisplayCurrentTime:
    """Tests for _display_current_time method."""

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    @patch("src.farmer_cli.features.configuration.console")
    def test_display_current_time(self, mock_console):
        """Test current time display."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        feature = ConfigurationFeature()
        feature._display_current_time()

        mock_console.clear.assert_called_once()
        # Should print multiple time formats
        assert mock_console.print.call_count >= 5


class TestThemeShowcase:
    """Tests for _theme_showcase method."""

    @patch("src.farmer_cli.features.configuration.THEMES", {"default": {"name": "Default"}})
    @patch("src.farmer_cli.features.theme_showcase.ThemeShowcaseFeature")
    def test_theme_showcase(self, mock_showcase_class):
        """Test theme showcase launch."""
        from src.farmer_cli.features.configuration import ConfigurationFeature

        mock_showcase = MagicMock()
        mock_showcase_class.return_value = mock_showcase

        feature = ConfigurationFeature()
        feature._theme_showcase()

        mock_showcase.execute.assert_called_once()
