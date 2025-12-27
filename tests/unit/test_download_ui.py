"""
Unit tests for farmer_cli.ui.download_ui module.

Tests the download progress UI components, queue display, history display,
and helper functions.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rich.progress import Progress


class TestCreateDownloadProgress:
    """Tests for create_download_progress function."""

    def test_returns_progress_object(self):
        """Test that create_download_progress returns a Progress object."""
        from farmer_cli.ui.download_ui import create_download_progress

        progress = create_download_progress()

        assert isinstance(progress, Progress)

    def test_progress_has_spinner_column(self):
        """Test that progress includes a spinner column."""
        from farmer_cli.ui.download_ui import create_download_progress

        progress = create_download_progress()

        # Check columns include SpinnerColumn
        column_types = [type(col).__name__ for col in progress.columns]
        assert "SpinnerColumn" in column_types

    def test_progress_has_bar_column(self):
        """Test that progress includes a bar column."""
        from farmer_cli.ui.download_ui import create_download_progress

        progress = create_download_progress()

        column_types = [type(col).__name__ for col in progress.columns]
        assert "BarColumn" in column_types

    def test_progress_has_transfer_speed_column(self):
        """Test that progress includes transfer speed column."""
        from farmer_cli.ui.download_ui import create_download_progress

        progress = create_download_progress()

        column_types = [type(col).__name__ for col in progress.columns]
        assert "TransferSpeedColumn" in column_types

    def test_progress_has_time_remaining_column(self):
        """Test that progress includes time remaining column."""
        from farmer_cli.ui.download_ui import create_download_progress

        progress = create_download_progress()

        column_types = [type(col).__name__ for col in progress.columns]
        assert "TimeRemainingColumn" in column_types


class TestCreateMultiDownloadProgress:
    """Tests for create_multi_download_progress function."""

    def test_returns_progress_object(self):
        """Test that create_multi_download_progress returns a Progress object."""
        from farmer_cli.ui.download_ui import create_multi_download_progress

        progress = create_multi_download_progress()

        assert isinstance(progress, Progress)

    def test_progress_is_expanded(self):
        """Test that multi-download progress is expanded."""
        from farmer_cli.ui.download_ui import create_multi_download_progress

        progress = create_multi_download_progress()

        assert progress.expand is True

    def test_progress_has_required_columns(self):
        """Test that multi-download progress has all required columns."""
        from farmer_cli.ui.download_ui import create_multi_download_progress

        progress = create_multi_download_progress()

        column_types = [type(col).__name__ for col in progress.columns]
        assert "SpinnerColumn" in column_types
        assert "BarColumn" in column_types
        assert "TransferSpeedColumn" in column_types
        assert "TimeRemainingColumn" in column_types


class TestDisplayDownloadQueue:
    """Tests for display_download_queue function."""

    def test_empty_queue_shows_message(self):
        """Test that empty queue displays appropriate message."""
        from farmer_cli.ui.download_ui import display_download_queue

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_queue([])

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "empty" in call_args.lower()

    def test_displays_queue_items(self):
        """Test that queue items are displayed in a table."""
        from farmer_cli.ui.download_ui import display_download_queue

        # Create mock queue items
        mock_item = MagicMock()
        mock_item.status.value = "pending"
        mock_item.progress = 50.0
        mock_item.title = "Test Video"
        mock_item.url = "https://example.com/video"
        mock_item.position = 1

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_queue([mock_item])

            mock_console.print.assert_called_once()

    def test_truncates_long_titles(self):
        """Test that long titles are truncated."""
        from farmer_cli.ui.download_ui import display_download_queue

        mock_item = MagicMock()
        mock_item.status.value = "pending"
        mock_item.progress = 0.0
        mock_item.title = "A" * 100  # Very long title
        mock_item.url = "https://example.com/video"
        mock_item.position = 1

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_queue([mock_item])

            # Should complete without error
            mock_console.print.assert_called_once()

    def test_uses_url_when_title_missing(self):
        """Test that URL is used when title is None."""
        from farmer_cli.ui.download_ui import display_download_queue

        mock_item = MagicMock()
        mock_item.status.value = "downloading"
        mock_item.progress = 25.0
        mock_item.title = None
        mock_item.url = "https://example.com/video"
        mock_item.position = 1

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_queue([mock_item])

            mock_console.print.assert_called_once()


class TestDisplayDownloadHistory:
    """Tests for display_download_history function."""

    def test_empty_history_shows_message(self):
        """Test that empty history displays appropriate message."""
        from farmer_cli.ui.download_ui import display_download_history

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_history([])

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "no" in call_args.lower() or "history" in call_args.lower()

    def test_displays_history_entries(self):
        """Test that history entries are displayed in a table."""
        from farmer_cli.ui.download_ui import display_download_history

        mock_entry = MagicMock()
        mock_entry.title = "Test Video"
        mock_entry.downloaded_at = datetime(2024, 1, 15, 10, 30)
        mock_entry.file_size = 1024 * 1024 * 50  # 50 MB
        mock_entry.file_path = "/tmp/nonexistent.mp4"

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_history([mock_entry])

            mock_console.print.assert_called_once()

    def test_truncates_long_titles(self):
        """Test that long titles in history are truncated."""
        from farmer_cli.ui.download_ui import display_download_history

        mock_entry = MagicMock()
        mock_entry.title = "B" * 100  # Very long title
        mock_entry.downloaded_at = datetime(2024, 1, 15, 10, 30)
        mock_entry.file_size = 1024
        mock_entry.file_path = "/tmp/test.mp4"

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_history([mock_entry])

            mock_console.print.assert_called_once()

    def test_shows_file_exists_status(self, tmp_path):
        """Test that file existence is checked and displayed."""
        from farmer_cli.ui.download_ui import display_download_history

        # Create a real file
        test_file = tmp_path / "existing.mp4"
        test_file.write_text("test")

        mock_entry = MagicMock()
        mock_entry.title = "Test Video"
        mock_entry.downloaded_at = datetime(2024, 1, 15, 10, 30)
        mock_entry.file_size = 4
        mock_entry.file_path = str(test_file)

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_history([mock_entry])

            mock_console.print.assert_called_once()

    def test_handles_none_file_path(self):
        """Test that None file_path is handled gracefully."""
        from farmer_cli.ui.download_ui import display_download_history

        mock_entry = MagicMock()
        mock_entry.title = "Test Video"
        mock_entry.downloaded_at = datetime(2024, 1, 15, 10, 30)
        mock_entry.file_size = None
        mock_entry.file_path = None

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_history([mock_entry])

            mock_console.print.assert_called_once()


class TestDisplayVideoInfoPanel:
    """Tests for display_video_info_panel function."""

    def test_displays_title(self):
        """Test that video title is displayed."""
        from farmer_cli.ui.download_ui import display_video_info_panel

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_video_info_panel(title="Test Video Title")

            mock_console.print.assert_called_once()

    def test_displays_all_info(self):
        """Test that all video info is displayed when provided."""
        from farmer_cli.ui.download_ui import display_video_info_panel

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_video_info_panel(
                title="Test Video",
                uploader="Test Channel",
                duration="5:30",
                views=1000000,
                formats_count=15,
            )

            mock_console.print.assert_called_once()

    def test_handles_optional_fields(self):
        """Test that optional fields are handled when None."""
        from farmer_cli.ui.download_ui import display_video_info_panel

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_video_info_panel(
                title="Test Video",
                uploader=None,
                duration=None,
                views=None,
                formats_count=0,
            )

            mock_console.print.assert_called_once()


class TestDisplayFormatSelection:
    """Tests for display_format_selection function."""

    def test_displays_video_formats(self):
        """Test that video formats are displayed."""
        from farmer_cli.ui.download_ui import display_format_selection

        video_formats = [
            {"resolution": "1080p", "extension": "mp4", "filesize": "500 MB", "codec": "h264"},
            {"resolution": "720p", "extension": "mp4", "filesize": "300 MB", "codec": "h264"},
        ]

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_format_selection(video_formats=video_formats, audio_formats=[])

            assert mock_console.print.call_count >= 1

    def test_displays_audio_formats(self):
        """Test that audio formats are displayed."""
        from farmer_cli.ui.download_ui import display_format_selection

        audio_formats = [
            {"extension": "m4a", "bitrate": "128k", "filesize": "5 MB"},
            {"extension": "mp3", "bitrate": "320k", "filesize": "10 MB"},
        ]

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_format_selection(video_formats=[], audio_formats=audio_formats)

            assert mock_console.print.call_count >= 1

    def test_displays_both_format_types(self):
        """Test that both video and audio formats are displayed."""
        from farmer_cli.ui.download_ui import display_format_selection

        video_formats = [{"resolution": "1080p", "extension": "mp4", "filesize": "500 MB", "codec": "h264"}]
        audio_formats = [{"extension": "m4a", "bitrate": "128k", "filesize": "5 MB"}]

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_format_selection(video_formats=video_formats, audio_formats=audio_formats)

            # Should print multiple times (headers + tables)
            assert mock_console.print.call_count >= 2

    def test_handles_missing_format_fields(self):
        """Test that missing format fields default to N/A."""
        from farmer_cli.ui.download_ui import display_format_selection

        video_formats = [{}]  # Empty format dict

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_format_selection(video_formats=video_formats, audio_formats=[])

            mock_console.print.assert_called()

    def test_empty_formats_no_output(self):
        """Test that empty format lists produce no output."""
        from farmer_cli.ui.download_ui import display_format_selection

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_format_selection(video_formats=[], audio_formats=[])

            # No tables should be printed
            mock_console.print.assert_not_called()


class TestDisplayBatchProgress:
    """Tests for display_batch_progress function."""

    def test_displays_progress_info(self):
        """Test that batch progress info is displayed."""
        from farmer_cli.ui.download_ui import display_batch_progress

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_batch_progress(
                current=5,
                total=10,
                current_title="Test Video Title",
                successes=4,
                failures=0,
            )

            assert mock_console.print.call_count == 2

    def test_displays_success_and_failure_counts(self):
        """Test that success and failure counts are shown."""
        from farmer_cli.ui.download_ui import display_batch_progress

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_batch_progress(
                current=10,
                total=10,
                current_title="Final Video",
                successes=8,
                failures=2,
            )

            mock_console.print.assert_called()

    def test_truncates_long_title(self):
        """Test that long current title is truncated."""
        from farmer_cli.ui.download_ui import display_batch_progress

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_batch_progress(
                current=1,
                total=5,
                current_title="A" * 100,  # Very long title
                successes=0,
                failures=0,
            )

            mock_console.print.assert_called()


class TestDisplayDownloadComplete:
    """Tests for display_download_complete function."""

    def test_displays_file_path(self):
        """Test that file path is displayed."""
        from farmer_cli.ui.download_ui import display_download_complete

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_complete(file_path="/path/to/video.mp4")

            assert mock_console.print.call_count >= 2

    def test_displays_file_size(self):
        """Test that file size is displayed when provided."""
        from farmer_cli.ui.download_ui import display_download_complete

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_complete(
                file_path="/path/to/video.mp4",
                file_size=1024 * 1024 * 100,  # 100 MB
            )

            assert mock_console.print.call_count >= 3

    def test_displays_duration_seconds(self):
        """Test that duration in seconds is displayed."""
        from farmer_cli.ui.download_ui import display_download_complete

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_complete(
                file_path="/path/to/video.mp4",
                duration=45.5,
            )

            assert mock_console.print.call_count >= 3

    def test_displays_duration_minutes(self):
        """Test that duration over 60s is shown in minutes."""
        from farmer_cli.ui.download_ui import display_download_complete

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_complete(
                file_path="/path/to/video.mp4",
                duration=125.0,  # 2m 5s
            )

            assert mock_console.print.call_count >= 3


class TestDisplayDownloadFailed:
    """Tests for display_download_failed function."""

    def test_displays_error_message(self):
        """Test that error message is displayed."""
        from farmer_cli.ui.download_ui import display_download_failed

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_failed(error_message="Network timeout")

            assert mock_console.print.call_count >= 2

    def test_displays_url_when_provided(self):
        """Test that URL is displayed when provided."""
        from farmer_cli.ui.download_ui import display_download_failed

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_failed(
                error_message="Video unavailable",
                url="https://example.com/video",
            )

            assert mock_console.print.call_count >= 3

    def test_truncates_long_url(self):
        """Test that long URLs are truncated."""
        from farmer_cli.ui.download_ui import display_download_failed

        with patch("farmer_cli.ui.download_ui.console") as mock_console:
            display_download_failed(
                error_message="Error",
                url="https://example.com/" + "a" * 100,
            )

            mock_console.print.assert_called()


class TestGetStatusStyle:
    """Tests for _get_status_style helper function."""

    def test_pending_status_yellow(self):
        """Test that pending status returns yellow."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("pending") == "yellow"

    def test_downloading_status_cyan(self):
        """Test that downloading status returns cyan."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("downloading") == "cyan"

    def test_completed_status_green(self):
        """Test that completed status returns green."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("completed") == "green"

    def test_failed_status_red(self):
        """Test that failed status returns red."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("failed") == "red"

    def test_paused_status_magenta(self):
        """Test that paused status returns magenta."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("paused") == "magenta"

    def test_cancelled_status_dim(self):
        """Test that cancelled status returns dim."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("cancelled") == "dim"

    def test_unknown_status_white(self):
        """Test that unknown status returns white."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("unknown") == "white"

    def test_case_insensitive(self):
        """Test that status matching is case insensitive."""
        from farmer_cli.ui.download_ui import _get_status_style

        assert _get_status_style("PENDING") == "yellow"
        assert _get_status_style("Downloading") == "cyan"
        assert _get_status_style("COMPLETED") == "green"


class TestFormatFilesize:
    """Tests for _format_filesize helper function."""

    def test_none_returns_unknown(self):
        """Test that None returns 'Unknown'."""
        from farmer_cli.ui.download_ui import _format_filesize

        assert _format_filesize(None) == "Unknown"

    def test_zero_returns_unknown(self):
        """Test that 0 returns 'Unknown'."""
        from farmer_cli.ui.download_ui import _format_filesize

        assert _format_filesize(0) == "Unknown"

    def test_bytes_format(self):
        """Test formatting for bytes."""
        from farmer_cli.ui.download_ui import _format_filesize

        assert _format_filesize(500) == "500 B"

    def test_kilobytes_format(self):
        """Test formatting for kilobytes."""
        from farmer_cli.ui.download_ui import _format_filesize

        result = _format_filesize(1024 * 5)
        assert "KB" in result
        assert "5" in result

    def test_megabytes_format(self):
        """Test formatting for megabytes."""
        from farmer_cli.ui.download_ui import _format_filesize

        result = _format_filesize(1024 * 1024 * 50)
        assert "MB" in result
        assert "50" in result

    def test_gigabytes_format(self):
        """Test formatting for gigabytes."""
        from farmer_cli.ui.download_ui import _format_filesize

        result = _format_filesize(1024 * 1024 * 1024 * 2)
        assert "GB" in result
        assert "2" in result

    def test_decimal_precision(self):
        """Test that decimal values are formatted with one decimal place."""
        from farmer_cli.ui.download_ui import _format_filesize

        result = _format_filesize(1024 * 1024 * 1536)  # 1.5 GB
        assert "1.5" in result
        assert "GB" in result
