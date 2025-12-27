"""Unit tests for file_browser.py feature module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFileBrowserFeature:
    """Tests for FileBrowserFeature class."""

    def test_init(self):
        """Test FileBrowserFeature initialization."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        feature = FileBrowserFeature()

        assert feature.name == "File Browser"

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        mock_choice.return_value = "back"

        feature = FileBrowserFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.choice_prompt")
    def test_execute_list_files(self, mock_choice, mock_console):
        """Test execute list files option."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        mock_choice.side_effect = ["list", "back"]

        feature = FileBrowserFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.choice_prompt")
    @patch("src.farmer_cli.features.file_browser.text_prompt")
    def test_execute_navigate(self, mock_text, mock_choice, mock_console):
        """Test execute navigate option."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        mock_choice.side_effect = ["navigate", "back"]
        mock_text.return_value = "."

        feature = FileBrowserFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.choice_prompt")
    @patch("src.farmer_cli.features.file_browser.text_prompt")
    def test_execute_search(self, mock_text, mock_choice, mock_console):
        """Test execute search option."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        mock_choice.side_effect = ["search", "back"]
        mock_text.return_value = "*.py"

        feature = FileBrowserFeature()
        feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.file_browser import FileBrowserFeature

        feature = FileBrowserFeature()
        # Should not raise
        feature.cleanup()


class TestListDirectory:
    """Tests for list_directory helper function."""

    def test_list_directory_current(self):
        """Test listing current directory."""
        from src.farmer_cli.features.file_browser import list_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "test.txt").write_text("test")

            result = list_directory(tmpdir)

            assert result is not None


class TestGetFileInfo:
    """Tests for get_file_info helper function."""

    def test_get_file_info(self):
        """Test getting file info."""
        from src.farmer_cli.features.file_browser import get_file_info

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            result = get_file_info(str(test_file))

            assert result is not None
