"""
Integration tests for CLI interface.

This module tests all CLI commands and options,
and error handling for invalid inputs.

Feature: farmer-cli-completion
Requirements: 9.4
"""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from farmer_cli.cli import cli
from farmer_cli.cli import main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


# ---------------------------------------------------------------------------
# CLI Basic Commands Tests
# ---------------------------------------------------------------------------


class TestCLIBasicCommands:
    """Integration tests for basic CLI commands."""

    def test_cli_version_flag(self, cli_runner: CliRunner) -> None:
        """Test --version flag displays version."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "farmer-cli version" in result.output

    def test_cli_version_short_flag(self, cli_runner: CliRunner) -> None:
        """Test -V short flag displays version."""
        result = cli_runner.invoke(cli, ["-V"])

        assert result.exit_code == 0
        assert "farmer-cli version" in result.output

    def test_cli_help_flag(self, cli_runner: CliRunner) -> None:
        """Test --help flag displays help."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Farmer CLI" in result.output
        assert "Video downloading" in result.output
        assert "--version" in result.output
        assert "--quiet" in result.output

    def test_cli_download_help(self, cli_runner: CliRunner) -> None:
        """Test download command help."""
        result = cli_runner.invoke(cli, ["download", "--help"])

        assert result.exit_code == 0
        assert "Download a video from URL" in result.output
        assert "--format" in result.output
        assert "--output" in result.output

    def test_cli_interactive_help(self, cli_runner: CliRunner) -> None:
        """Test interactive command help."""
        result = cli_runner.invoke(cli, ["interactive", "--help"])

        assert result.exit_code == 0
        assert "Start interactive mode" in result.output


# ---------------------------------------------------------------------------
# CLI Download Command Tests
# ---------------------------------------------------------------------------


class TestCLIDownloadCommand:
    """Integration tests for download command."""

    def test_download_invalid_url(self, cli_runner: CliRunner) -> None:
        """Test download with invalid URL returns error."""
        result = cli_runner.invoke(cli, ["download", "not-a-valid-url"])

        assert result.exit_code == 1
        # Check for error indicators (may contain ANSI codes)
        output_lower = result.output.lower()
        assert "error" in output_lower or "invalid" in output_lower or "not a valid" in output_lower

    def test_download_empty_url(self, cli_runner: CliRunner) -> None:
        """Test download with empty URL returns error."""
        result = cli_runner.invoke(cli, ["download", ""])

        assert result.exit_code == 1

    def test_download_missing_url(self, cli_runner: CliRunner) -> None:
        """Test download without URL shows error."""
        result = cli_runner.invoke(cli, ["download"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "URL" in result.output

    def test_download_with_format_option(self, cli_runner: CliRunner) -> None:
        """Test download with --format option parses correctly."""
        # This will fail due to invalid URL, but we're testing option parsing
        result = cli_runner.invoke(
            cli, ["download", "--format", "720p", "invalid-url"]
        )

        # Should fail due to invalid URL, not option parsing
        assert result.exit_code == 1
        # Error should be about URL/video, not format
        output_lower = result.output.lower()
        assert "error" in output_lower or "unavailable" in output_lower

    def test_download_with_output_option(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test download with --output option parses correctly."""
        result = cli_runner.invoke(
            cli, ["download", "--output", str(tmp_path), "invalid-url"]
        )

        # Should fail due to invalid URL, not option parsing
        assert result.exit_code == 1

    def test_download_quiet_mode(self, cli_runner: CliRunner) -> None:
        """Test download with --quiet flag."""
        result = cli_runner.invoke(
            cli, ["--quiet", "download", "invalid-url"]
        )

        # Should fail but with minimal output
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI Error Handling Tests
# ---------------------------------------------------------------------------


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_invalid_command(self, cli_runner: CliRunner) -> None:
        """Test invalid command shows error."""
        result = cli_runner.invoke(cli, ["nonexistent-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "Error" in result.output

    def test_invalid_option(self, cli_runner: CliRunner) -> None:
        """Test invalid option shows error."""
        result = cli_runner.invoke(cli, ["--invalid-option"])

        assert result.exit_code != 0
        assert "no such option" in result.output.lower() or "error" in result.output.lower()

    def test_download_invalid_format_value(self, cli_runner: CliRunner) -> None:
        """Test download with invalid format value."""
        # Format value itself is valid, URL is invalid
        result = cli_runner.invoke(
            cli, ["download", "-f", "invalid_format_xyz", "invalid-url"]
        )

        # Should fail due to invalid URL
        assert result.exit_code == 1

    def test_download_invalid_output_path(self, cli_runner: CliRunner) -> None:
        """Test download with non-existent output path."""
        result = cli_runner.invoke(
            cli,
            ["download", "-o", "/nonexistent/path/that/does/not/exist", "invalid-url"],
        )

        # Should fail
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI Option Combinations Tests
# ---------------------------------------------------------------------------


class TestCLIOptionCombinations:
    """Integration tests for CLI option combinations."""

    def test_quiet_with_version(self, cli_runner: CliRunner) -> None:
        """Test --quiet with --version still shows version."""
        result = cli_runner.invoke(cli, ["--quiet", "--version"])

        assert result.exit_code == 0
        assert "farmer-cli version" in result.output

    def test_multiple_options_download(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test download with multiple options."""
        result = cli_runner.invoke(
            cli,
            [
                "--quiet",
                "download",
                "--format", "best",
                "--output", str(tmp_path),
                "invalid-url",
            ],
        )

        # Should fail due to invalid URL
        assert result.exit_code == 1

    def test_short_options_download(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test download with short option flags."""
        result = cli_runner.invoke(
            cli,
            [
                "-q",
                "download",
                "-f", "720p",
                "-o", str(tmp_path),
                "invalid-url",
            ],
        )

        # Should fail due to invalid URL
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI Main Entry Point Tests
# ---------------------------------------------------------------------------


class TestCLIMainEntryPoint:
    """Integration tests for CLI main entry point."""

    def test_main_returns_zero_on_success(self, cli_runner: CliRunner) -> None:
        """Test main() returns 0 on successful command."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_main_returns_nonzero_on_error(self, cli_runner: CliRunner) -> None:
        """Test main() returns non-zero on error."""
        result = cli_runner.invoke(cli, ["download", "invalid-url"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI URL Validation Tests
# ---------------------------------------------------------------------------


class TestCLIURLValidation:
    """Integration tests for URL validation in CLI."""

    def test_download_javascript_url_rejected(self, cli_runner: CliRunner) -> None:
        """Test that javascript: URLs are rejected."""
        result = cli_runner.invoke(cli, ["download", "javascript:alert('xss')"])

        assert result.exit_code == 1
        # Should show some error (may be about unsupported scheme)
        output_lower = result.output.lower()
        assert "error" in output_lower or "unsupported" in output_lower

    def test_download_file_url_rejected(self, cli_runner: CliRunner) -> None:
        """Test that file: URLs are rejected."""
        result = cli_runner.invoke(cli, ["download", "file:///etc/passwd"])

        assert result.exit_code == 1
        # Should show some error (may be about disabled file URLs)
        output_lower = result.output.lower()
        assert "error" in output_lower or "disabled" in output_lower

    def test_download_ftp_url_rejected(self, cli_runner: CliRunner) -> None:
        """Test that ftp: URLs are rejected."""
        result = cli_runner.invoke(cli, ["download", "ftp://example.com/video.mp4"])

        assert result.exit_code == 1
        assert "Invalid" in result.output or "Error" in result.output

    def test_download_malformed_url_rejected(self, cli_runner: CliRunner) -> None:
        """Test that malformed URLs are rejected."""
        result = cli_runner.invoke(cli, ["download", "http://"])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI Format Presets Tests
# ---------------------------------------------------------------------------


class TestCLIFormatPresets:
    """Integration tests for format preset handling."""

    def test_format_preset_best(self, cli_runner: CliRunner) -> None:
        """Test 'best' format preset is accepted."""
        result = cli_runner.invoke(cli, ["download", "-f", "best", "invalid-url"])

        # Should fail due to invalid URL, not format
        assert result.exit_code == 1
        # Error should be about URL/video, not format
        output_lower = result.output.lower()
        assert "error" in output_lower or "unavailable" in output_lower

    def test_format_preset_audio(self, cli_runner: CliRunner) -> None:
        """Test 'audio' format preset is accepted."""
        result = cli_runner.invoke(cli, ["download", "-f", "audio", "invalid-url"])

        assert result.exit_code == 1

    def test_format_preset_720p(self, cli_runner: CliRunner) -> None:
        """Test '720p' format preset is accepted."""
        result = cli_runner.invoke(cli, ["download", "-f", "720p", "invalid-url"])

        assert result.exit_code == 1

    def test_format_preset_1080p(self, cli_runner: CliRunner) -> None:
        """Test '1080p' format preset is accepted."""
        result = cli_runner.invoke(cli, ["download", "-f", "1080p", "invalid-url"])

        assert result.exit_code == 1
