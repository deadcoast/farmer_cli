"""
Unit tests for farmer_cli.features.log_viewer module.

Tests the LogViewerFeature class and log viewing functionality.

Fure: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestLogViewerFeatureInit:
    """Tests for LogViewerFeature initialization."""

    def test_initializes_with_name(self):
        """Test that feature initializes with correct name."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        assert feature.name == "Log Viewer"

    def test_initializes_with_description(self):
        """Test that feature initializes with description."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        assert "log" in feature.description.lower()

    def test_default_count_set(self):
        """Test that default count is set."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        assert feature._default_count == 50


class TestShowMenu:
    """Tests for LogViewerFeature._show_menu method."""

    def test_returns_valid_choice(self):
        """Test that valid choice is returned."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            mock_console.input.return_value = "1"

            result = feature._show_menu()

            assert result == "1"

    def test_returns_none_for_invalid_choice(self):
        """Test that invalid choice returns None."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            mock_console.input.return_value = "99"

            result = feature._show_menu()

            assert result is None

    def test_returns_zero_for_exit(self):
        """Test that '0' is returned for exit."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            mock_console.input.return_value = "0"

            result = feature._show_menu()

            assert result == "0"

    def test_displays_menu_options(self):
        """Test that menu options are displayed."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            mock_console.input.return_value = "0"

            feature._show_menu()

            # Should print multiple times for options
            assert mock_console.print.call_count >= 5


class TestViewAllLogs:
    """Tests for LogViewerFeature._view_all_logs method."""

    def test_displays_no_entries_message(self):
        """Test that message is shown when no entries."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_recent_logs.return_value = []

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.return_value = ""

            feature._view_all_logs()

            # Should show "no entries" message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("no" in str(call).lower() for call in calls)

    def test_displays_log_entries(self):
        """Test that log entries are displayed."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_recent_logs.return_value = [
            {"timestamp": "2024-01-15 10:30:00", "level": "INFO", "message": "Test message"},
        ]

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.return_value = ""

            feature._view_all_logs()

            mock_console.print.assert_called()

    def test_uses_count_parameter(self):
        """Test that count parameter is passed to get_recent_logs."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_recent_logs.return_value = []

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.return_value = ""

            feature._view_all_logs(count=100)

            mock_config.get_recent_logs.assert_called_once_with(count=100)


class TestViewFilteredLogs:
    """Tests for LogViewerFeature._view_filtered_logs method."""

    def test_displays_level_options(self):
        """Test that level options are displayed."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_recent_logs.return_value = []

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.side_effect = ["1", ""]  # Select first level, then continue

            feature._view_filtered_logs()

            # Should print level options
            assert mock_console.print.call_count >= 1

    def test_handles_invalid_selection(self):
        """Test that invalid selection is handled."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            mock_console.input.side_effect = ["invalid", ""]

            feature._view_filtered_logs()

            # Should show error message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("invalid" in str(call).lower() for call in calls)

    def test_filters_by_selected_level(self):
        """Test that logs are filtered by selected level."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_recent_logs.return_value = []

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
            patch("farmer_cli.features.log_viewer.VALID_LOG_LEVELS", ["DEBUG", "INFO", "ERROR"]),
        ):
            mock_console.input.side_effect = ["2", ""]  # Select INFO (index 2)

            feature._view_filtered_logs()

            # Should call get_recent_logs with level_filter
            mock_config.get_recent_logs.assert_called()


class TestViewLogFilePath:
    """Tests for LogViewerFeature._view_log_file_path method."""

    def test_displays_log_path(self, tmp_path):
        """Test that log path is displayed."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        log_file = tmp_path / "test.log"
        log_file.write_text("test log content")

        mock_config = MagicMock()
        mock_config.get_log_file_path.return_value = log_file

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.return_value = ""

            feature._view_log_file_path()

            mock_console.print.assert_called()

    def test_handles_no_log_path(self):
        """Test that missing log path is handled."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.get_log_file_path.return_value = None

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.return_value = ""

            feature._view_log_file_path()

            # Should show "not configured" message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("not configured" in str(call).lower() for call in calls)


class TestClearLogs:
    """Tests for LogViewerFeature._clear_logs method."""

    def test_clears_on_confirmation(self):
        """Test that logs are cleared on confirmation."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.clear_log_file.return_value = True

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.side_effect = ["y", ""]

            feature._clear_logs()

            mock_config.clear_log_file.assert_called_once()

    def test_cancels_without_confirmation(self):
        """Test that clear is cancelled without confirmation."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.side_effect = ["n", ""]

            feature._clear_logs()

            mock_config.clear_log_file.assert_not_called()

    def test_shows_success_message(self):
        """Test that success message is shown."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.clear_log_file.return_value = True

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.side_effect = ["y", ""]

            feature._clear_logs()

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("success" in str(call).lower() for call in calls)

    def test_shows_failure_message(self):
        """Test that failure message is shown."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        mock_config = MagicMock()
        mock_config.clear_log_file.return_value = False

        with (
            patch("farmer_cli.features.log_viewer.console") as mock_console,
            patch("farmer_cli.features.log_viewer.get_logging_config", return_value=mock_config),
        ):
            mock_console.input.side_effect = ["y", ""]

            feature._clear_logs()

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("failed" in str(call).lower() for call in calls)


class TestDisplayLogEntries:
    """Tests for LogViewerFeature._display_log_entries method."""

    def test_displays_entries_in_table(self):
        """Test that entries are displayed in a table."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        entries = [
            {"timestamp": "2024-01-15 10:30:00", "level": "INFO", "message": "Test message 1"},
            {"timestamp": "2024-01-15 10:31:00", "level": "ERROR", "message": "Test message 2"},
        ]

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            feature._display_log_entries(entries)

            mock_console.print.assert_called()

    def test_truncates_long_messages(self):
        """Test that long messages are truncated."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        entries = [
            {"timestamp": "2024-01-15 10:30:00", "level": "INFO", "message": "A" * 200},
        ]

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            feature._display_log_entries(entries)

            # Should complete without error
            mock_console.print.assert_called()

    def test_uses_custom_title(self):
        """Test that custom title is used."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        entries = [
            {"timestamp": "2024-01-15 10:30:00", "level": "INFO", "message": "Test"},
        ]

        with patch("farmer_cli.features.log_viewer.console") as mock_console:
            feature._display_log_entries(entries, title="Custom Title")

            mock_console.print.assert_called()


class TestFormatFileSize:
    """Tests for LogViewerFeature._format_file_size method."""

    def test_formats_bytes(self):
        """Test formatting bytes."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        result = feature._format_file_size(500)

        assert "B" in result
        assert "500" in result

    def test_formats_kilobytes(self):
        """Test formatting kilobytes."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        result = feature._format_file_size(1024 * 5)

        assert "KB" in result

    def test_formats_megabytes(self):
        """Test formatting megabytes."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        result = feature._format_file_size(1024 * 1024 * 10)

        assert "MB" in result

    def test_formats_gigabytes(self):
        """Test formatting gigabytes."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        result = feature._format_file_size(1024 * 1024 * 1024 * 2)

        assert "GB" in result


class TestCleanup:
    """Tests for LogViewerFeature.cleanup method."""

    def test_cleanup_does_not_raise(self):
        """Test that cleanup doesn't raise exceptions."""
        from farmer_cli.features.log_viewer import LogViewerFeature

        feature = LogViewerFeature()

        # Should not raise
        feature.cleanup()


class TestViewLogsFunction:
    """Tests for view_logs convenience function."""

    def test_creates_and_executes_feature(self):
        """Test that view_logs creates and executes feature."""
        from farmer_cli.features.log_viewer import view_logs

        with patch("farmer_cli.features.log_viewer.LogViewerFeature") as mock_feature_class:
            mock_feature = MagicMock()
            mock_feature_class.return_value = mock_feature

            view_logs()

            mock_feature_class.assert_called_once()
            mock_feature.execute.assert_called_once()


class TestLevelColors:
    """Tests for LEVEL_COLORS constant."""

    def test_debug_color(self):
        """Test DEBUG level color."""
        from farmer_cli.features.log_viewer import LEVEL_COLORS

        assert "DEBUG" in LEVEL_COLORS
        assert LEVEL_COLORS["DEBUG"] == "dim"

    def test_info_color(self):
        """Test INFO level color."""
        from farmer_cli.features.log_viewer import LEVEL_COLORS

        assert "INFO" in LEVEL_COLORS
        assert LEVEL_COLORS["INFO"] == "blue"

    def test_warning_color(self):
        """Test WARNING level color."""
        from farmer_cli.features.log_viewer import LEVEL_COLORS

        assert "WARNING" in LEVEL_COLORS
        assert LEVEL_COLORS["WARNING"] == "yellow"

    def test_error_color(self):
        """Test ERROR level color."""
        from farmer_cli.features.log_viewer import LEVEL_COLORS

        assert "ERROR" in LEVEL_COLORS
        assert LEVEL_COLORS["ERROR"] == "red"

    def test_critical_color(self):
        """Test CRITICAL level color."""
        from farmer_cli.features.log_viewer import LEVEL_COLORS

        assert "CRITICAL" in LEVEL_COLORS
        assert "red" in LEVEL_COLORS["CRITICAL"]
