"""Unit tests for layouts.py module."""

import pytest
from rich.layout import Layout


class TestCreateMainLayout:
    """Tests for create_main_layout function."""

    def test_create_main_layout(self):
        """Test creating main layout."""
        from src.farmer_cli.ui.layouts import create_main_layout

        result = create_main_layout()

        assert result is not None
        assert isinstance(result, Layout)

    def test_create_main_layout_has_sections(self):
        """Test main layout has header, body, footer sections."""
        from src.farmer_cli.ui.layouts import create_main_layout

        result = create_main_layout()

        # Layout should have named sections
        assert "header" in [child.name for child in result.children]
        assert "body" in [child.name for child in result.children]
        assert "footer" in [child.name for child in result.children]


class TestCreateSplitLayout:
    """Tests for create_split_layout function."""

    def test_create_split_layout(self):
        """Test creating split layout."""
        from src.farmer_cli.ui.layouts import create_split_layout

        result = create_split_layout("Left content", "Right content")

        assert result is not None
        assert isinstance(result, Layout)

    def test_create_split_layout_with_ratio(self):
        """Test creating split layout with custom ratio."""
        from src.farmer_cli.ui.layouts import create_split_layout

        result = create_split_layout("Left", "Right", split_ratio=0.3)

        assert result is not None


class TestCreateDashboardLayout:
    """Tests for create_dashboard_layout function."""

    def test_create_dashboard_layout(self):
        """Test creating dashboard layout."""
        from src.farmer_cli.ui.layouts import create_dashboard_layout

        result = create_dashboard_layout()

        assert result is not None
        assert isinstance(result, Layout)


class TestUpdateLayoutFooter:
    """Tests for update_layout_footer function."""

    def test_update_layout_footer(self):
        """Test updating layout footer."""
        from src.farmer_cli.ui.layouts import create_main_layout, update_layout_footer

        layout = create_main_layout()
        update_layout_footer(layout, "New footer text")

        # Should not raise

    def test_update_layout_footer_with_style(self):
        """Test updating layout footer with style."""
        from src.farmer_cli.ui.layouts import create_main_layout, update_layout_footer

        layout = create_main_layout()
        update_layout_footer(layout, "Styled footer", style="bold red")

        # Should not raise

    def test_update_layout_footer_no_footer(self):
        """Test updating layout without footer section."""
        from src.farmer_cli.ui.layouts import update_layout_footer
        from rich.layout import Layout

        layout = Layout()
        # Should not raise even without footer
        update_layout_footer(layout, "Text")


class TestUpdateLayoutHeader:
    """Tests for update_layout_header function."""

    def test_update_layout_header(self):
        """Test updating layout header."""
        from src.farmer_cli.ui.layouts import create_main_layout, update_layout_header

        layout = create_main_layout()
        update_layout_header(layout, "New header text")

        # Should not raise

    def test_update_layout_header_with_style(self):
        """Test updating layout header with style."""
        from src.farmer_cli.ui.layouts import create_main_layout, update_layout_header

        layout = create_main_layout()
        update_layout_header(layout, "Styled header", style="bold green")

        # Should not raise
