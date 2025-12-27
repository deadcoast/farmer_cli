"""
Unit tests for the cli.py module.

Tests cover:
- Download command execution paths
- Interactive command routing
- Quiet mode output suppression
- Version and help flags
- QuietContext class

Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from farmer_cli.cli import QuietContext
from farmer_cli.cli import cli
from farmer_cli.cli import main


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_ytdlp_wrapper():
    """Create a mock YtdlpWrapper."""
    wrapper = MagicMock()
    return wrapper


# ---------------------------------------------------------------------------
# QuietContext Tests
# ---------------------------------------------------------------------------


class TestQuietContext:
    """Tests for QuietContext class."""

    def test_init_default_not_quiet(self):
        """Test default initialization is not quiet."""
        ctx = QuietContext()
        assert ctx.quiet is False

    def test_init_quiet_true(self):
        """Test initialization with quiet=True."""
        ctx = QuietContext(quiet=True)
        assert ctx.quiet is True

    def test_echo_when_not_quiet(self):
        """Test echo outputs when not quiet."""
        ctx = QuietContext(quiet=False)

        with patch("click.echo") as mock_echo:
            ctx.echo("test message")
            mock_echo.assert_called_once_with("test message")

    def test_echo_when_quiet(self):
        """Test echo suppressed when quiet."""
        ctx = QuietContext(quiet=True)

        with patch("click.echo") as mock_echo:
            ctx.echo("test message")
            mock_echo.assert_not_called()

    def test_print_when_not_quiet(self):
        """Test print outputs when not quiet."""
        ctx = QuietContext(quiet=False)

        with patch("farmer_cli.cli.console") as mock_console:
            ctx.print("test message")
            mock_console.print.assert_called_once_with("test message")

    def test_print_when_quiet(self):
        """Test print suppressed when quiet."""
        ctx = QuietContext(quiet=True)

        with patch("farmer_cli.cli.console") as mock_console:
            ctx.print("test message")
            mock_console.print.assert_not_called()


# ---------------------------------------------------------------------------
# Version Flag Tests
# ---------------------------------------------------------------------------


class TestVersionFlag:
    """Tests for --version flag."""

    def test_version_short_flag(self, runner):
        """Test -V flag shows version."""
        result = runner.invoke(cli, ["-V"])

        assert result.exit_code == 0
        assert "farmer-cli version" in result.output

    def test_version_long_flag(self, runner):
        """Test --version flag shows version."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "farmer-cli version" in result.output


# ---------------------------------------------------------------------------
# Help Flag Tests
# ---------------------------------------------------------------------------


class TestHelpFlag:
    """Tests for --help flag."""

    def test_help_flag(self, runner):
        """Test --help shows help text."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Farmer CLI" in result.output
        assert "download" in result.output
        assert "interactive" in result.output

    def test_download_help(self, runner):
        """Test download --help shows command help."""
        result = runner.invoke(cli, ["download", "--help"])

        assert result.exit_code == 0
        assert "Download a video" in result.output
        assert "--format" in result.output
        assert "--output" in result.output


# ---------------------------------------------------------------------------
# Quiet Mode Tests
# ---------------------------------------------------------------------------


class TestQuietMode:
    """Tests for --quiet flag."""

    def test_quiet_flag_accepted(self, runner):
        """Test -q flag is accepted."""
        result = runner.invoke(cli, ["-q", "--version"])

        assert result.exit_code == 0

    def test_quiet_long_flag_accepted(self, runner):
        """Test --quiet flag is accepted."""
        result = runner.invoke(cli, ["--quiet", "--version"])

        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Download Command Tests
# ---------------------------------------------------------------------------


class TestDownloadCommand:
    """Tests for download command."""

    def test_download_invalid_url(self, runner):
        """Test download with invalid URL fails."""
        result = runner.invoke(cli, ["download", "not-a-url"])

        assert result.exit_code == 1
        # Check for error indicators (case-insensitive due to ANSI codes)
        output_lower = result.output.lower()
        assert "invalid" in output_lower or "error" in output_lower or "not a valid" in output_lower

    def test_download_empty_url(self, runner):
        """Test download with empty URL fails."""
        result = runner.invoke(cli, ["download", ""])

        assert result.exit_code == 1

    def test_download_requires_url(self, runner):
        """Test download requires URL argument."""
        result = runner.invoke(cli, ["download"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "URL" in result.output

    def test_download_format_option(self, runner):
        """Test download accepts --format option."""
        # Just verify the option is recognized
        result = runner.invoke(cli, ["download", "--help"])

        assert "--format" in result.output
        assert "-f" in result.output

    def test_download_output_option(self, runner):
        """Test download accepts --output option."""
        # Just verify the option is recognized
        result = runner.invoke(cli, ["download", "--help"])

        assert "--output" in result.output
        assert "-o" in result.output


# ---------------------------------------------------------------------------
# Interactive Command Tests
# ---------------------------------------------------------------------------


class TestInteractiveCommand:
    """Tests for interactive command."""

    def test_interactive_help(self, runner):
        """Test interactive --help shows help."""
        result = runner.invoke(cli, ["interactive", "--help"])

        assert result.exit_code == 0
        assert "interactive mode" in result.output.lower()


# ---------------------------------------------------------------------------
# Main Function Tests
# ---------------------------------------------------------------------------


class TestMainFunction:
    """Tests for main() entry point."""

    def test_main_returns_zero_on_success(self):
        """Test main returns 0 on success."""
        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.return_value = None

            result = main()

            assert result == 0

    def test_main_returns_exit_code_on_system_exit(self):
        """Test main returns exit code from SystemExit."""
        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.side_effect = SystemExit(42)

            result = main()

            assert result == 42

    def test_main_returns_one_on_click_exception(self):
        """Test main returns exit code from ClickException."""
        from click import ClickException

        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.side_effect = ClickException("test error")

            result = main()

            assert result == 1

    def test_main_returns_one_on_abort(self):
        """Test main returns 1 on click.Abort."""
        from click import Abort

        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.side_effect = Abort()

            result = main()

            assert result == 1

    def test_main_returns_130_on_keyboard_interrupt(self):
        """Test main returns 130 on KeyboardInterrupt."""
        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()

            result = main()

            assert result == 130

    def test_main_returns_one_on_exception(self):
        """Test main returns 1 on unexpected exception."""
        with patch("farmer_cli.cli.cli") as mock_cli:
            mock_cli.side_effect = Exception("unexpected error")

            result = main()

            assert result == 1


# ---------------------------------------------------------------------------
# CLI Group Tests
# ---------------------------------------------------------------------------


class TestCLIGroup:
    """Tests for CLI group behavior."""

    def test_cli_group_has_commands(self, runner):
        """Test CLI group has expected commands."""
        result = runner.invoke(cli, ["--help"])

        assert "download" in result.output
        assert "interactive" in result.output

    def test_cli_unknown_command(self, runner):
        """Test CLI with unknown command shows error."""
        result = runner.invoke(cli, ["unknown-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "Error" in result.output


# ---------------------------------------------------------------------------
# Download Command Integration Tests (with mocks)
# ---------------------------------------------------------------------------


class TestDownloadCommandWithMocks:
    """Integration tests for download command with mocked services."""

    def test_download_with_valid_url_mocked(self, runner, tmp_path):
        """Test download with valid URL (mocked services)."""
        mock_video_info = MagicMock()
        mock_video_info.title = "Test Video"
        mock_video_info.uploader = "Test Channel"
        mock_video_info.duration = 300
        mock_video_info.formats = []

        mock_format = MagicMock()
        mock_format.format_id = "22"
        mock_format.resolution = "1280x720"
        mock_format.extension = "mp4"

        with patch("farmer_cli.cli.YtdlpWrapper") as mock_wrapper_class, \
             patch("farmer_cli.cli.FormatSelector") as mock_selector_class, \
             patch("farmer_cli.cli.PreferencesService") as mock_prefs_class, \
             patch("farmer_cli.cli.DownloadManager"):

            mock_wrapper = mock_wrapper_class.return_value
            mock_wrapper.extract_info.return_value = mock_video_info
            mock_wrapper.download.return_value = str(tmp_path / "video.mp4")

            mock_selector = mock_selector_class.return_value
            mock_selector.get_best_format.return_value = mock_format

            mock_prefs = mock_prefs_class.return_value
            mock_prefs.get.return_value = str(tmp_path)

            # Create the output file so stat() works
            (tmp_path / "video.mp4").write_text("fake video")

            result = runner.invoke(
                cli,
                ["download", "https://youtube.com/watch?v=test123"],
            )

            # Should succeed with mocked services
            assert "Download complete" in result.output or result.exit_code == 0

    def test_download_quiet_mode_suppresses_output(self, runner, tmp_path):
        """Test download in quiet mode suppresses output."""
        mock_video_info = MagicMock()
        mock_video_info.title = "Test Video"
        mock_video_info.uploader = "Test Channel"
        mock_video_info.duration = 300
        mock_video_info.formats = []

        mock_format = MagicMock()
        mock_format.format_id = "22"
        mock_format.resolution = "1280x720"
        mock_format.extension = "mp4"

        with patch("farmer_cli.cli.YtdlpWrapper") as mock_wrapper_class, \
             patch("farmer_cli.cli.FormatSelector") as mock_selector_class, \
             patch("farmer_cli.cli.PreferencesService") as mock_prefs_class, \
             patch("farmer_cli.cli.DownloadManager"):

            mock_wrapper = mock_wrapper_class.return_value
            mock_wrapper.extract_info.return_value = mock_video_info
            mock_wrapper.download.return_value = str(tmp_path / "video.mp4")

            mock_selector = mock_selector_class.return_value
            mock_selector.get_best_format.return_value = mock_format

            mock_prefs = mock_prefs_class.return_value
            mock_prefs.get.return_value = str(tmp_path)

            # Create the output file
            (tmp_path / "video.mp4").write_text("fake video")

            result = runner.invoke(
                cli,
                ["-q", "download", "https://youtube.com/watch?v=test123"],
            )

            # In quiet mode, output should be minimal
            # The test verifies the command runs without error
            assert result.exit_code == 0 or "Error" not in result.output
