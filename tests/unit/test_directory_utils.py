"""Unit tests for directory_utils.py module."""

import pytest
import tempfile
from pathlib import Path


class TestValidateDirectory:
    """Tests for validate_directory function."""

    def test_validate_directory_valid(self):
        """Test validating a valid directory."""
        from src.farmer_cli.utils.directory_utils import validate_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_directory(tmpdir)

            assert result.is_valid is True
            assert result.exists is True
            assert result.is_writable is True
            assert result.error is None

    def test_validate_directory_nonexistent(self):
        """Test validating a nonexistent directory."""
        from src.farmer_cli.utils.directory_utils import validate_directory

        result = validate_directory("/nonexistent/path/that/does/not/exist")

        assert result.is_valid is False
        assert result.exists is False
        assert result.error is not None

    def test_validate_directory_file_not_dir(self):
        """Test validating a file path (not directory)."""
        from src.farmer_cli.utils.directory_utils import validate_directory

        with tempfile.NamedTemporaryFile() as tmpfile:
            result = validate_directory(tmpfile.name)

            assert result.is_valid is False
            assert result.exists is True
            assert "not a directory" in result.error.lower()


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_ensure_directory_creates_new(self):
        """Test ensure_directory creates new directory."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_directory"

            result = ensure_directory(str(new_dir))

            assert result.is_valid is True
            assert new_dir.exists()

    def test_ensure_directory_existing(self):
        """Test ensure_directory with existing directory."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory(tmpdir)

            assert result.is_valid is True

    def test_ensure_directory_nested(self):
        """Test ensure_directory creates nested directories."""
        from src.farmer_cli.utils.directory_utils import ensure_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "level1" / "level2" / "level3"

            result = ensure_directory(str(nested_dir))

            assert result.is_valid is True
            assert nested_dir.exists()


class TestIsPathWritable:
    """Tests for is_path_writable function."""

    def test_is_path_writable_true(self):
        """Test is_path_writable returns True for writable directory."""
        from src.farmer_cli.utils.directory_utils import is_path_writable

        with tempfile.TemporaryDirectory() as tmpdir:
            result = is_path_writable(tmpdir)

            assert result is True

    def test_is_path_writable_nonexistent_parent_writable(self):
        """Test is_path_writable for nonexistent path with writable parent."""
        from src.farmer_cli.utils.directory_utils import is_path_writable

        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"
            result = is_path_writable(str(nonexistent))

            assert result is True


class TestGetAvailableSpace:
    """Tests for get_available_space function."""

    def test_get_available_space(self):
        """Test getting available space."""
        from src.farmer_cli.utils.directory_utils import get_available_space

        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_available_space(tmpdir)

            assert result is not None
            assert result > 0

    def test_get_available_space_nonexistent(self):
        """Test getting available space for nonexistent path."""
        from src.farmer_cli.utils.directory_utils import get_available_space

        # Should return None or find parent
        result = get_available_space("/completely/nonexistent/path/xyz")

        # Result depends on whether any parent exists
        # Just verify it doesn't raise


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_normalize_path(self):
        """Test normalizing a path."""
        from src.farmer_cli.utils.directory_utils import normalize_path

        result = normalize_path("./test")

        assert result is not None
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_normalize_path_with_home(self):
        """Test normalizing path with home directory."""
        from src.farmer_cli.utils.directory_utils import normalize_path

        result = normalize_path("~/test")

        assert result is not None
        assert "~" not in str(result)


class TestIsSubdirectory:
    """Tests for is_subdirectory function."""

    def test_is_subdirectory_true(self):
        """Test is_subdirectory returns True for subdirectory."""
        from src.farmer_cli.utils.directory_utils import is_subdirectory

        with tempfile.TemporaryDirectory() as tmpdir:
            child = Path(tmpdir) / "child"
            child.mkdir()

            result = is_subdirectory(str(child), tmpdir)

            assert result is True

    def test_is_subdirectory_false(self):
        """Test is_subdirectory returns False for non-subdirectory."""
        from src.farmer_cli.utils.directory_utils import is_subdirectory

        result = is_subdirectory("/tmp", "/var")

        assert result is False

    def test_is_subdirectory_same_path(self):
        """Test is_subdirectory returns True for same path."""
        from src.farmer_cli.utils.directory_utils import is_subdirectory

        with tempfile.TemporaryDirectory() as tmpdir:
            result = is_subdirectory(tmpdir, tmpdir)

            assert result is True
