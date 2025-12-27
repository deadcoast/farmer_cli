"""Unit tests for directory_utils.py module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_ensure_directory_creates_new(self):
        """Test ensure_directory creates new directory."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_directory"

            result = ensure_directory(str(new_dir))

            assert result is True
            assert new_dir.exists()

    def test_ensure_directory_existing(self):
        """Test ensure_directory with existing directory."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory(tmpdir)

            assert result is True

    def test_ensure_directory_nested(self):
        """Test ensure_directory creates nested directories."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "level1" / "level2" / "level3"

            result = ensure_directory(str(nested_dir))

            assert result is True
            assert nested_dir.exists()


class TestIsWritable:
    """Tests for is_writable function."""

    def test_is_writable_true(self):
        """Test is_writable returns True for writable directory."""
        from src.farmer_cli.utils.directory_utils import is_writable

        with tempfile.TemporaryDirectory() as tmpdir:
            result = is_writable(tmpdir)

            assert result is True

    def test_is_writable_nonexistent(self):
        """Test is_writable returns False for nonexistent directory."""
        from src.farmer_cli.utils.directory_utils import is_writable

        result = is_writable("/nonexistent/path/that/does/not/exist")

        assert result is False


class TestGetDirectorySize:
    """Tests for get_directory_size function."""

    def test_get_directory_size_empty(self):
        """Test get_directory_size for empty directory."""
        from src.farmer_cli.utils.directory_utils import get_directory_size

        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_directory_size(tmpdir)

            assert result == 0

    def test_get_directory_size_with_files(self):
        """Test get_directory_size with files."""
        from src.farmer_cli.utils.directory_utils import get_directory_size

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")

            result = get_directory_size(tmpdir)

            assert result > 0


class TestListFiles:
    """Tests for list_files function."""

    def test_list_files_all(self):
        """Test list_files returns all files."""
        from src.farmer_cli.utils.directory_utils import list_files

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.py").write_text("content2")

            result = list_files(tmpdir)

            assert len(result) == 2

    def test_list_files_with_pattern(self):
        """Test list_files with pattern filter."""
        from src.farmer_cli.utils.directory_utils import list_files

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.py").write_text("content2")

            result = list_files(tmpdir, pattern="*.txt")

            assert len(result) == 1
            assert "file1.txt" in str(result[0])

    def test_list_files_empty_directory(self):
        """Test list_files on empty directory."""
        from src.farmer_cli.utils.directory_utils import list_files

        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_files(tmpdir)

            assert result == []


class TestGetRelativePath:
    """Tests for get_relative_path function."""

    def test_get_relative_path(self):
        """Test get_relative_path returns relative path."""
        from src.farmer_cli.utils.directory_utils import get_relative_path

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "file.txt"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("content")

            result = get_relative_path(str(file_path), tmpdir)

            assert "subdir" in result
            assert "file.txt" in result


class TestCopyDirectory:
    """Tests for copy_directory function."""

    def test_copy_directory(self):
        """Test copy_directory copies all contents."""
        from src.farmer_cli.utils.directory_utils import copy_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "source"
            src_dir.mkdir()
            (src_dir / "file.txt").write_text("content")

            dst_dir = Path(tmpdir) / "destination"

            copy_directory(str(src_dir), str(dst_dir))

            assert dst_dir.exists()
            assert (dst_dir / "file.txt").exists()


class TestDeleteDirectory:
    """Tests for delete_directory function."""

    def test_delete_directory(self):
        """Test delete_directory removes directory."""
        from src.farmer_cli.utils.directory_utils import delete_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_to_delete = Path(tmpdir) / "to_delete"
            dir_to_delete.mkdir()
            (dir_to_delete / "file.txt").write_text("content")

            delete_directory(str(dir_to_delete))

            assert not dir_to_delete.exists()
