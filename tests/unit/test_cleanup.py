"""Unit tests for cleanup.py module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCleanupTempFiles:
    """Tests for cleanup_temp_files function."""

    def test_cleanup_temp_files_removes_files(self):
        """Test cleanup_temp_files removes temporary files."""
        from src.farmer_cli.utils.cleanup import cleanup_temp_files

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some temp files
            temp_file = Path(tmpdir) / "test.tmp"
            temp_file.write_text("test")

            cleanup_temp_files(tmpdir, pattern="*.tmp")

            assert not temp_file.exists()

    def test_cleanup_temp_files_no_matching_files(self):
        """Test cleanup_temp_files with no matching files."""
        from src.farmer_cli.utils.cleanup import cleanup_temp_files

        with tempfile.TemporaryDirectory() as tmpdir:
            # No files to clean
            result = cleanup_temp_files(tmpdir, pattern="*.nonexistent")

            # Should not raise

    def test_cleanup_temp_files_nonexistent_directory(self):
        """Test cleanup_temp_files with nonexistent directory."""
        from src.farmer_cli.utils.cleanup import cleanup_temp_files

        # Should not raise
        cleanup_temp_files("/nonexistent/path", pattern="*.tmp")


class TestCleanupOldLogs:
    """Tests for cleanup_old_logs function."""

    def test_cleanup_old_logs_removes_old_files(self):
        """Test cleanup_old_logs removes old log files."""
        from src.farmer_cli.utils.cleanup import cleanup_old_logs

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a log file
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("log content")

            # Set modification time to old
            old_time = 0  # Very old
            os.utime(log_file, (old_time, old_time))

            cleanup_old_logs(tmpdir, max_age_days=0)

            assert not log_file.exists()

    def test_cleanup_old_logs_keeps_recent_files(self):
        """Test cleanup_old_logs keeps recent log files."""
        from src.farmer_cli.utils.cleanup import cleanup_old_logs

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a recent log file
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("log content")

            cleanup_old_logs(tmpdir, max_age_days=30)

            assert log_file.exists()


class TestCleanupCache:
    """Tests for cleanup_cache function."""

    def test_cleanup_cache_clears_directory(self):
        """Test cleanup_cache clears cache directory."""
        from src.farmer_cli.utils.cleanup import cleanup_cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()

            cache_file = cache_dir / "cached_data.json"
            cache_file.write_text("{}")

            cleanup_cache(str(cache_dir))

            # Cache directory should be empty or file removed
            assert not cache_file.exists() or not list(cache_dir.iterdir())


class TestPerformFullCleanup:
    """Tests for perform_full_cleanup function."""

    @patch("src.farmer_cli.utils.cleanup.cleanup_temp_files")
    @patch("src.farmer_cli.utils.cleanup.cleanup_old_logs")
    @patch("src.farmer_cli.utils.cleanup.cleanup_cache")
    def test_perform_full_cleanup(self, mock_cache, mock_logs, mock_temp):
        """Test perform_full_cleanup calls all cleanup functions."""
        from src.farmer_cli.utils.cleanup import perform_full_cleanup

        with tempfile.TemporaryDirectory() as tmpdir:
            perform_full_cleanup(tmpdir)

            # All cleanup functions should be called
            mock_temp.assert_called()
            mock_logs.assert_called()
            mock_cache.assert_called()
