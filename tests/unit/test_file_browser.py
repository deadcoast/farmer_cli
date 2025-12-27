"""Tests for file_browser.py module."""

import stat
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestBrowseFiles:
    """Tests for browse_files function."""

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.text_prompt")
    @patch("src.farmer_cli.features.file_browser.list_directory")
    def test_browse_files_success(self, mock_list_dir, mock_prompt, mock_console):
        """Test successful file browsing."""
        from src.farmer_cli.features.file_browser import browse_files

        mock_prompt.return_value = "."
        browse_files()

        mock_console.clear.assert_called_once()
        mock_list_dir.assert_called_once()

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.text_prompt")
    @patch("src.farmer_cli.features.file_browser.list_directory")
    def test_browse_files_error(self, mock_list_dir, mock_prompt, mock_console):
        """Test file browsing with error."""
        from src.farmer_cli.features.file_browser import browse_files

        mock_prompt.return_value = "."
        mock_list_dir.side_effect = Exception("Test error")

        browse_files()

        mock_console.print.assert_called()


class TestListDirectory:
    """Tests for list_directory function."""

    @patch("src.farmer_cli.features.file_browser.console")
    def test_list_directory_not_a_dir(self, mock_console, tmp_path):
        """Test listing a file instead of directory."""
        from src.farmer_cli.features.file_browser import list_directory

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        list_directory(test_file)

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.file_browser.console")
    def test_list_directory_empty(self, mock_console, tmp_path):
        """Test listing empty directory."""
        from src.farmer_cli.features.file_browser import list_directory

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        list_directory(empty_dir)

        # Should print empty message
        assert mock_console.print.called

    @patch("src.farmer_cli.features.file_browser.console")
    @patch("src.farmer_cli.features.file_browser.create_table")
    def test_list_directory_with_files(self, mock_table, mock_console, tmp_path):
        """Test listing directory with files."""
        from src.farmer_cli.features.file_browser import list_directory

        # Create test files
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.py").write_text("code")
        (tmp_path / "subdir").mkdir()

        mock_table.return_value = MagicMock()

        list_directory(tmp_path)

        mock_table.assert_called_once()
        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.file_browser.console")
    def test_list_directory_permission_error(self, mock_console, tmp_path):
        """Test listing directory with permission error."""
        from src.farmer_cli.features.file_browser import list_directory

        # Create a mock path that raises PermissionError
        mock_path = MagicMock(spec=Path)
        mock_path.is_dir.return_value = True
        mock_path.iterdir.side_effect = PermissionError("Access denied")

        list_directory(mock_path)

        mock_console.print.assert_called()


class TestGetFileInfo:
    """Tests for get_file_info function."""

    def test_get_file_info_regular_file(self, tmp_path):
        """Test getting info for regular file."""
        from src.farmer_cli.features.file_browser import get_file_info

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        info = get_file_info(test_file)

        assert len(info) == 5
        assert info[0] == "test.txt"
        assert info[1] == "TXT"

    def test_get_file_info_directory(self, tmp_path):
        """Test getting info for directory."""
        from src.farmer_cli.features.file_browser import get_file_info

        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        info = get_file_info(test_dir)

        assert info[0] == "testdir/"
        assert info[1] == "Dir"
        assert info[2] == "-"

    def test_get_file_info_no_extension(self, tmp_path):
        """Test getting info for file without extension."""
        from src.farmer_cli.features.file_browser import get_file_info

        test_file = tmp_path / "README"
        test_file.write_text("content")

        info = get_file_info(test_file)

        assert info[0] == "README"
        assert info[1] == "File"

    def test_get_file_info_error(self):
        """Test getting info with error."""
        from src.farmer_cli.features.file_browser import get_file_info

        # Non-existent path
        mock_path = MagicMock(spec=Path)
        mock_path.name = "test.txt"
        mock_path.stat.side_effect = Exception("Error")

        info = get_file_info(mock_path)

        assert info[0] == "test.txt"
        assert info[1] == "?"


class TestFormatSize:
    """Tests for format_size function."""

    def test_format_size_bytes(self):
        """Test formatting bytes."""
        from src.farmer_cli.features.file_browser import format_size

        assert "B" in format_size(100)

    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        from src.farmer_cli.features.file_browser import format_size

        assert "KB" in format_size(2048)

    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        from src.farmer_cli.features.file_browser import format_size

        assert "MB" in format_size(2 * 1024 * 1024)

    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        from src.farmer_cli.features.file_browser import format_size

        assert "GB" in format_size(2 * 1024 * 1024 * 1024)


class TestFormatPermissions:
    """Tests for format_permissions function."""

    def test_format_permissions_full(self):
        """Test formatting full permissions."""
        from src.farmer_cli.features.file_browser import format_permissions

        # rwxrwxrwx = 0o777
        mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        result = format_permissions(mode)

        assert result == "rwxrwxrwx"

    def test_format_permissions_read_only(self):
        """Test formatting read-only permissions."""
        from src.farmer_cli.features.file_browser import format_permissions

        # r--r--r-- = 0o444
        mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        result = format_permissions(mode)

        assert result == "r--r--r--"

    def test_format_permissions_none(self):
        """Test formatting no permissions."""
        from src.farmer_cli.features.file_browser import format_permissions

        result = format_permissions(0)

        assert result == "---------"
