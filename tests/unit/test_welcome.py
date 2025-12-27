"""Unit tests for welcome.py module."""

import pytest
from unittest.mock import patch, MagicMock
from rich.text import Text
from rich.align import Align


class TestDisplayWelcomeScreen:
    """Tests for display_welcome_screen function."""

    @patch("src.farmer_cli.ui.welcome.console")
    def test_display_welcome_screen_default_theme(self, mock_console):
        """Test welcome screen with default theme."""
        from src.farmer_cli.ui.welcome import display_welcome_screen

        display_welcome_screen()

        # Verify console methods were called
        assert mock_console.clear.called
        assert mock_console.print.called

    @patch("src.farmer_cli.ui.welcome.console")
    def test_display_welcome_screen_custom_theme(self, mock_console):
        """Test welcome screen with custom theme."""
        from src.farmer_cli.ui.welcome import display_welcome_screen

        display_welcome_screen(theme="ocean", app_name="Test App", version="1.0.0")

        assert mock_console.clear.called
        assert mock_console.print.called

    @patch("src.farmer_cli.ui.welcome.console")
    def test_display_welcome_screen_invalid_theme_falls_back(self, mock_console):
        """Test welcome screen falls back to default for invalid theme."""
        from src.farmer_cli.ui.welcome import display_welcome_screen

        display_welcome_screen(theme="nonexistent_theme")

        assert mock_console.clear.called


class TestCreateStatusLine:
    """Tests for create_status_line function."""

    def test_create_status_line_basic(self):
        """Test basic status line creation."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status")

        assert isinstance(result, Text)
        assert "Test status" in str(result)

    def test_create_status_line_with_icon(self):
        """Test status line with icon."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", icon="bullet")

        assert isinstance(result, Text)

    def test_create_status_line_with_invalid_icon(self):
        """Test status line with invalid icon falls back gracefully."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", icon="nonexistent_icon")

        assert isinstance(result, Text)
        assert "Test status" in str(result)

    def test_create_status_line_center_align(self):
        """Test status line with center alignment."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", align="center")

        assert isinstance(result, Align)

    def test_create_status_line_right_align(self):
        """Test status line with right alignment."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", align="right")

        assert isinstance(result, Align)

    def test_create_status_line_left_align(self):
        """Test status line with left alignment (default)."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", align="left")

        assert isinstance(result, Text)

    def test_create_status_line_custom_theme(self):
        """Test status line with custom theme."""
        from src.farmer_cli.ui.welcome import create_status_line

        result = create_status_line("Test status", theme="ocean")

        assert isinstance(result, Text)


class TestCreateDivider:
    """Tests for create_divider function."""

    def test_create_divider_default(self):
        """Test default divider creation."""
        from src.farmer_cli.ui.welcome import create_divider

        result = create_divider()

        assert isinstance(result, str)
        assert len(result) == 60

    def test_create_divider_custom_width(self):
        """Test divider with custom width."""
        from src.farmer_cli.ui.welcome import create_divider

        result = create_divider(width=40)

        assert len(result) == 40

    def test_create_divider_with_text(self):
        """Test divider with centered text."""
        from src.farmer_cli.ui.welcome import create_divider

        result = create_divider(width=60, text="Section")

        assert "Section" in result
        assert len(result) == 60

    def test_create_divider_custom_theme(self):
        """Test divider with custom theme."""
        from src.farmer_cli.ui.welcome import create_divider

        result = create_divider(theme="ocean")

        assert isinstance(result, str)
