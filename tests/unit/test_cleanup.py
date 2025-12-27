"""Tests for cleanup.py module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestRegisterCleanup:
    """Tests for register_cleanup function."""

    def test_register_cleanup(self):
        """Test registering a cleanup handler."""
        from src.farmer_cli.utils.cleanup import _cleanup_handlers, register_cleanup

        initial_count = len(_cleanup_handlers)
        handler = MagicMock()

        register_cleanup(handler)

        assert len(_cleanup_handlers) == initial_count + 1
        assert handler in _cleanup_handlers

        # Clean up
        _cleanup_handlers.remove(handler)


class TestRunCleanupHandler:
    """Tests for _run_cleanup_handler function."""

    def test_run_cleanup_handler_success(self):
        """Test running a successful cleanup handler."""
        from src.farmer_cli.utils.cleanup import _run_cleanup_handler

        handler = MagicMock()
        _run_cleanup_handler(handler)

        handler.assert_called_once()

    @patch("src.farmer_cli.utils.cleanup.logger")
    def test_run_cleanup_handler_error(self, mock_logger):
        """Test running a cleanup handler that raises an error."""
        from src.farmer_cli.utils.cleanup import _run_cleanup_handler

        handler = MagicMock(side_effect=Exception("Test error"))
        _run_cleanup_handler(handler)

        handler.assert_called_once()
        mock_logger.error.assert_called_once()


class TestCleanupHandler:
    """Tests for cleanup_handler function."""

    @patch("src.farmer_cli.utils.cleanup.console")
    @patch("src.farmer_cli.utils.cleanup.PreferencesService")
    @patch("src.farmer_cli.utils.cleanup.get_database_manager")
    @patch("src.farmer_cli.utils.cleanup._cleanup_handlers", [])
    def test_cleanup_handler_success(self, mock_db, mock_prefs_class, mock_console):
        """Test successful cleanup."""
        from src.farmer_cli.utils.cleanup import cleanup_handler

        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {}
        mock_prefs_class.return_value = mock_prefs

        mock_db_manager = MagicMock()
        mock_db.return_value = mock_db_manager

        cleanup_handler()

        mock_console.print.assert_called()
        mock_prefs.save.assert_called_once()
        mock_db_manager.close.assert_called_once()

    @patch("src.farmer_cli.utils.cleanup.console")
    @patch("src.farmer_cli.utils.cleanup.PreferencesService")
    @patch("src.farmer_cli.utils.cleanup.get_database_manager")
    @patch("src.farmer_cli.utils.cleanup.logger")
    @patch("src.farmer_cli.utils.cleanup._cleanup_handlers", [])
    def test_cleanup_handler_prefs_error(self, mock_logger, mock_db, mock_prefs_class, mock_console):
        """Test cleanup with preferences error."""
        from src.farmer_cli.utils.cleanup import cleanup_handler

        mock_prefs_class.side_effect = Exception("Prefs error")
        mock_db_manager = MagicMock()
        mock_db.return_value = mock_db_manager

        cleanup_handler()

        mock_logger.error.assert_called()

    @patch("src.farmer_cli.utils.cleanup.console")
    @patch("src.farmer_cli.utils.cleanup.PreferencesService")
    @patch("src.farmer_cli.utils.cleanup.get_database_manager")
    @patch("src.farmer_cli.utils.cleanup.logger")
    @patch("src.farmer_cli.utils.cleanup._cleanup_handlers", [])
    def test_cleanup_handler_db_error(self, mock_logger, mock_db, mock_prefs_class, mock_console):
        """Test cleanup with database error."""
        from src.farmer_cli.utils.cleanup import cleanup_handler

        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {}
        mock_prefs_class.return_value = mock_prefs

        mock_db.side_effect = Exception("DB error")

        cleanup_handler()

        mock_logger.error.assert_called()

    @patch("src.farmer_cli.utils.cleanup.console")
    @patch("src.farmer_cli.utils.cleanup.PreferencesService")
    @patch("src.farmer_cli.utils.cleanup.get_database_manager")
    @patch("src.farmer_cli.utils.cleanup._run_cleanup_handler")
    def test_cleanup_handler_runs_registered_handlers(
        self, mock_run_handler, mock_db, mock_prefs_class, mock_console
    ):
        """Test that registered handlers are called."""
        from src.farmer_cli.utils.cleanup import _cleanup_handlers, cleanup_handler

        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {}
        mock_prefs_class.return_value = mock_prefs

        mock_db_manager = MagicMock()
        mock_db.return_value = mock_db_manager

        # Add a test handler
        test_handler = MagicMock()
        _cleanup_handlers.append(test_handler)

        try:
            cleanup_handler()
            mock_run_handler.assert_called()
        finally:
            _cleanup_handlers.remove(test_handler)


class TestCleanupTempFiles:
    """Tests for cleanup_temp_files function."""

    @patch("src.farmer_cli.utils.cleanup.logger")
    def test_cleanup_temp_files_no_files(self, mock_logger, tmp_path, monkeypatch):
        """Test cleanup when no temp files exist."""
        from src.farmer_cli.utils import cleanup

        # Patch the constant to a non-existent file
        monkeypatch.setattr("src.farmer_cli.core.constants.HTML_TEMP_FILE", str(tmp_path / "nonexistent.html"))

        cleanup.cleanup_temp_files()

        # Should not log any warnings since files don't exist
        mock_logger.warning.assert_not_called()

    @patch("src.farmer_cli.utils.cleanup.logger")
    def test_cleanup_temp_files_with_files(self, mock_logger, tmp_path, monkeypatch):
        """Test cleanup when temp files exist."""
        from src.farmer_cli.utils import cleanup

        # Create actual temp files
        temp_html = tmp_path / "temp.html"
        temp_html.write_text("test")

        # Patch the constant to use our temp path
        monkeypatch.setattr("src.farmer_cli.core.constants.HTML_TEMP_FILE", str(temp_html))

        cleanup.cleanup_temp_files()

        # File should be removed
        assert not temp_html.exists()

    @patch("src.farmer_cli.utils.cleanup.logger")
    def test_cleanup_temp_files_unlink_error(self, mock_logger, tmp_path, monkeypatch):
        """Test cleanup when unlink fails."""
        from pathlib import Path
        from src.farmer_cli.utils import cleanup

        # Create a temp file
        temp_html = tmp_path / "temp.html"
        temp_html.write_text("test")

        # Patch the constant
        monkeypatch.setattr("src.farmer_cli.core.constants.HTML_TEMP_FILE", str(temp_html))

        # Make the file read-only to cause unlink to fail (on some systems)
        # Instead, we'll patch Path to raise an error
        original_path = Path

        class MockPath(type(Path())):
            def __new__(cls, *args, **kwargs):
                return original_path(*args, **kwargs)

            def unlink(self):
                raise OSError("Permission denied")

        # Use a simpler approach - just verify the function handles errors
        with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
            cleanup.cleanup_temp_files()

        mock_logger.warning.assert_called()
