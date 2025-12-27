"""Unit tests for widgets.py module."""

import pytest
from rich.text import Text
from rich.table import Table


class TestCreateFrame:
    """Tests for create_frame function."""

    def test_create_frame_basic(self):
        """Test creating basic frame."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Content")

        assert result is not None
        assert isinstance(result, Text)

    def test_create_frame_with_title(self):
        """Test creating frame with title."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Content", title="Title")

        assert result is not None
        assert "Title" in result.plain

    def test_create_frame_with_width(self):
        """Test creating frame with custom width."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Content", width=40)

        assert result is not None

    def test_create_frame_with_theme(self):
        """Test creating frame with theme."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Content", theme="default")

        assert result is not None

    def test_create_frame_with_padding(self):
        """Test creating frame with padding."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Content", padding=4)

        assert result is not None

    def test_create_frame_multiline_content(self):
        """Test creating frame with multiline content."""
        from src.farmer_cli.ui.widgets import create_frame

        result = create_frame("Line 1\nLine 2\nLine 3")

        assert result is not None


class TestCreateTable:
    """Tests for create_table function."""

    def test_create_table_basic(self):
        """Test creating basic table."""
        from src.farmer_cli.ui.widgets import create_table

        columns = [("Name", {}), ("Value", {})]
        rows = [["Item 1", "100"], ["Item 2", "200"]]

        result = create_table("Test Table", columns, rows)

        assert result is not None
        assert isinstance(result, Table)

    def test_create_table_with_options(self):
        """Test creating table with options."""
        from src.farmer_cli.ui.widgets import create_table

        columns = [("Name", {"style": "bold"}), ("Value", {"justify": "right"})]
        rows = [["Item 1", "100"]]

        result = create_table(
            "Test Table",
            columns,
            rows,
            show_header=True,
            show_lines=True,
            style="blue"
        )

        assert result is not None


class TestCreateCustomProgressBar:
    """Tests for create_custom_progress_bar function."""

    def test_create_custom_progress_bar_basic(self):
        """Test creating basic progress bar."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100)

        assert result is not None
        assert isinstance(result, str)

    def test_create_custom_progress_bar_with_label(self):
        """Test creating progress bar with label."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, label="Progress")

        assert result is not None
        assert "Progress" in result

    def test_create_custom_progress_bar_with_percentage(self):
        """Test creating progress bar with percentage."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, show_percentage=True)

        assert result is not None
        assert "50" in result

    def test_create_custom_progress_bar_without_percentage(self):
        """Test creating progress bar without percentage."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, show_percentage=False)

        assert result is not None

    def test_create_custom_progress_bar_custom_width(self):
        """Test creating progress bar with custom width."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, width=30)

        assert result is not None

    def test_create_custom_progress_bar_with_theme(self):
        """Test creating progress bar with theme."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, theme="default")

        assert result is not None

    def test_create_custom_progress_bar_zero_total(self):
        """Test creating progress bar with zero total."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=0, total=0)

        assert result is not None

    def test_create_custom_progress_bar_complete(self):
        """Test creating complete progress bar."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=100, total=100)

        assert result is not None
        assert "100" in result

    def test_create_custom_progress_bar_with_numbers(self):
        """Test creating progress bar with numbers."""
        from src.farmer_cli.ui.widgets import create_custom_progress_bar

        result = create_custom_progress_bar(current=50, total=100, show_numbers=True)

        assert result is not None
        assert "50" in result
        assert "100" in result


class TestShowProgress:
    """Tests for show_progress function."""

    def test_show_progress(self):
        """Test show_progress returns Progress object."""
        from src.farmer_cli.ui.widgets import show_progress
        from rich.progress import Progress

        result = show_progress("Processing...")

        assert result is not None
        assert isinstance(result, Progress)

    def test_show_progress_with_total(self):
        """Test show_progress with total."""
        from src.farmer_cli.ui.widgets import show_progress

        result = show_progress("Processing...", total=100)

        assert result is not None


class TestCreateSpinner:
    """Tests for create_spinner function."""

    def test_create_spinner(self):
        """Test create_spinner returns Live object."""
        from src.farmer_cli.ui.widgets import create_spinner
        from rich.live import Live

        result = create_spinner("Loading...")

        assert result is not None
        assert isinstance(result, Live)

    def test_create_spinner_default_text(self):
        """Test create_spinner with default text."""
        from src.farmer_cli.ui.widgets import create_spinner

        result = create_spinner()

        assert result is not None
