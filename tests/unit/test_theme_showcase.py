"""Unit tests for theme_showcase.py module."""

import pytest
from unittest.mock import patch, MagicMock


class TestThemeShowcaseFeature:
    """Tests for ThemeShowcaseFeature class."""

    def test_init(self):
        """Test ThemeShowcaseFeature initialization."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        feature = ThemeShowcaseFeature()

        assert feature.name == "Theme Showcase"
        assert "demonstration" in feature.description.lower()

    @patch("src.farmer_cli.features.theme_showcase.console")
    @patch("src.farmer_cli.features.theme_showcase.confirm_prompt")
    def test_execute_user_declines(self, mock_confirm, mock_console):
        """Test execute when user declines to see themes."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        mock_confirm.return_value = False

        feature = ThemeShowcaseFeature()
        feature.execute()

        mock_console.clear.assert_called()
        mock_confirm.assert_called_once()

    @patch("src.farmer_cli.features.theme_showcase.console")
    @patch("src.farmer_cli.features.theme_showcase.confirm_prompt")
    @patch("src.farmer_cli.features.theme_showcase.THEMES")
    def test_execute_shows_themes(self, mock_themes, mock_confirm, mock_console):
        """Test execute shows themes when user accepts."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        # Setup mock themes
        mock_themes.__iter__ = MagicMock(return_value=iter(["default"]))
        mock_themes.items.return_value = [
            ("default", {
                "name": "Default",
                "description": "Default theme",
                "title_style": "bold",
                "subtitle_style": "dim",
                "header_style": "bold blue",
                "success_style": "green",
                "error_style": "red",
                "warning_style": "yellow",
                "info_style": "cyan",
                "prompt_style": "bold",
                "option_style": "white",
                "border_style": "blue",
                "table_row_style": "white",
                "table_header_style": "bold white on blue",
            })
        ]
        mock_themes.keys.return_value = ["default"]
        mock_themes.get.return_value = mock_themes.items.return_value[0][1]

        # First confirm to see themes, then stop after first theme
        mock_confirm.side_effect = [True]

        feature = ThemeShowcaseFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.theme_showcase.console")
    @patch("src.farmer_cli.features.theme_showcase.confirm_prompt")
    @patch("src.farmer_cli.features.theme_showcase.THEMES")
    def test_execute_stops_on_user_request(self, mock_themes, mock_confirm, mock_console):
        """Test execute stops when user declines to continue."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        # Setup mock themes with multiple themes
        mock_themes.__iter__ = MagicMock(return_value=iter(["default", "ocean"]))
        mock_themes.items.return_value = [
            ("default", {
                "name": "Default",
                "description": "Default theme",
                "title_style": "bold",
                "subtitle_style": "dim",
                "header_style": "bold blue",
                "success_style": "green",
                "error_style": "red",
                "warning_style": "yellow",
                "info_style": "cyan",
                "prompt_style": "bold",
                "option_style": "white",
                "border_style": "blue",
                "table_row_style": "white",
                "table_header_style": "bold white on blue",
            }),
            ("ocean", {
                "name": "Ocean",
                "description": "Ocean theme",
                "title_style": "bold cyan",
                "subtitle_style": "dim cyan",
                "header_style": "bold blue",
                "success_style": "green",
                "error_style": "red",
                "warning_style": "yellow",
                "info_style": "cyan",
                "prompt_style": "bold",
                "option_style": "white",
                "border_style": "cyan",
                "table_row_style": "white",
                "table_header_style": "bold white on cyan",
            })
        ]
        mock_themes.keys.return_value = ["default", "ocean"]
        mock_themes.get.return_value = mock_themes.items.return_value[0][1]

        # Accept to see themes, then decline to continue
        mock_confirm.side_effect = [True, False]

        feature = ThemeShowcaseFeature()
        feature.execute()

        # Should have been called at least twice
        assert mock_confirm.call_count >= 1

    def test_cleanup(self):
        """Test cleanup method does nothing."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        feature = ThemeShowcaseFeature()
        # Should not raise
        feature.cleanup()

    @patch("src.farmer_cli.features.theme_showcase.console")
    @patch("src.farmer_cli.features.theme_showcase.create_frame")
    @patch("src.farmer_cli.features.theme_showcase.create_custom_progress_bar")
    def test_showcase_theme(self, mock_progress, mock_frame, mock_console):
        """Test _showcase_theme method."""
        from src.farmer_cli.features.theme_showcase import ThemeShowcaseFeature

        mock_frame.return_value = "frame"
        mock_progress.return_value = "progress"

        theme_data = {
            "name": "Test",
            "description": "Test theme",
            "title_style": "bold",
            "subtitle_style": "dim",
            "header_style": "bold blue",
            "success_style": "green",
            "error_style": "red",
            "warning_style": "yellow",
            "info_style": "cyan",
            "prompt_style": "bold",
            "option_style": "white",
            "border_style": "blue",
            "table_row_style": "white",
            "table_header_style": "bold white on blue",
        }

        feature = ThemeShowcaseFeature()
        feature._showcase_theme("test", theme_data)

        mock_console.clear.assert_called()
        mock_console.print.assert_called()
