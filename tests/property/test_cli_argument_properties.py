"""
Property-based tests for CLI argument handling.

Feature: farmer-cli-completion
Property 18: CLI Invalid Argument Handling
Validates: Requirements 13.6

For any invalid combination of CLI arguments, the application SHALL exit
with a non-zero code and display usage help.
"""

import string

import pytest
from click.testing import CliRunner
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st


# Import the CLI module under test
from farmer_cli.cli import cli
from farmer_cli.cli import download


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating invalid URLs
invalid_url_strategy = st.one_of(
    st.just(""),  # Empty string
    st.just("   "),  # Whitespace only
    st.text(min_size=1, max_size=50).filter(lambda x: "://" not in x),  # No scheme
    st.sampled_from([
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "file:///etc/passwd",
        "vbscript:msgbox('xss')",
        "not-a-url",
        "random-text",
        "http://",
        "https://",
        "://missing-scheme.com",
    ]),
)

# Strategy for generating invalid format options
invalid_format_strategy = st.one_of(
    st.text(
        alphabet=string.ascii_letters + string.digits + "!@#$%^&*()",
        min_size=1,
        max_size=20,
    ).filter(lambda x: x.lower() not in ("best", "1080p", "720p", "480p", "360p", "audio")),
)

# Strategy for generating invalid output paths
invalid_output_path_strategy = st.sampled_from([
    "/nonexistent/deeply/nested/path/that/does/not/exist",
    "\x00invalid",  # Null byte in path
    "",  # Empty path
])

# Strategy for generating unknown CLI options
unknown_option_strategy = st.sampled_from([
    "--unknown-option",
    "--invalid",
    "-x",
    "-Z",
    "--foo=bar",
    "--nonexistent",
])


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestCLIInvalidArgumentHandling:
    """
    Property 18: CLI Invalid Argument Handling

    For any invalid combination of CLI arguments, the application SHALL exit
    with a non-zero code and display usage help.

    **Validates: Requirements 13.6**
    """

    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    @given(invalid_url_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.property
    def test_invalid_urls_exit_with_nonzero_code(self, invalid_url: str):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.6

        For any invalid URL provided to the download command, the CLI SHALL
        exit with a non-zero code.
        """
        runner = CliRunner()

        # Run the download command with an invalid URL
        result = runner.invoke(cli, ["download", invalid_url])

        # Should exit with non-zero code for invalid URLs
        assert result.exit_code != 0, (
            f"Invalid URL '{invalid_url}' should cause non-zero exit code, "
            f"got {result.exit_code}"
        )

    @given(unknown_option_strategy)
    @settings(max_examples=50)
    @pytest.mark.property
    def test_unknown_options_exit_with_nonzero_code(self, unknown_option: str):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.6

        For any unknown CLI option, the application SHALL exit with a non-zero
        code and display usage help.
        """
        runner = CliRunner()

        # Run the CLI with an unknown option
        result = runner.invoke(cli, [unknown_option])

        # Should exit with non-zero code for unknown options
        assert result.exit_code != 0, (
            f"Unknown option '{unknown_option}' should cause non-zero exit code, "
            f"got {result.exit_code}"
        )

        # Should display usage information or error message
        output_lower = result.output.lower()
        assert (
            "error" in output_lower
            or "usage" in output_lower
            or "no such option" in output_lower
            or "invalid" in output_lower
        ), f"Output should contain error or usage info, got: {result.output}"

    @given(unknown_option_strategy)
    @settings(max_examples=50)
    @pytest.mark.property
    def test_download_unknown_options_exit_with_nonzero_code(self, unknown_option: str):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.6

        For any unknown option to the download command, the CLI SHALL exit
        with a non-zero code.
        """
        runner = CliRunner()

        # Run the download command with an unknown option
        result = runner.invoke(cli, ["download", unknown_option, "https://example.com/video"])

        # Should exit with non-zero code for unknown options
        assert result.exit_code != 0, (
            f"Unknown option '{unknown_option}' should cause non-zero exit code, "
            f"got {result.exit_code}"
        )

    @pytest.mark.property
    def test_download_missing_url_exits_with_nonzero_code(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.6

        When the download command is invoked without a URL argument, the CLI
        SHALL exit with a non-zero code and display usage help.
        """
        runner = CliRunner()

        # Run the download command without a URL
        result = runner.invoke(cli, ["download"])

        # Should exit with non-zero code
        assert result.exit_code != 0, (
            f"Missing URL should cause non-zero exit code, got {result.exit_code}"
        )

        # Should display usage information
        output_lower = result.output.lower()
        assert (
            "error" in output_lower
            or "usage" in output_lower
            or "missing" in output_lower
            or "argument" in output_lower
        ), f"Output should contain error or usage info, got: {result.output}"

    @pytest.mark.property
    def test_version_flag_exits_with_zero_code(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.5

        When the --version flag is provided, the CLI SHALL display version
        information and exit with code 0.
        """
        runner = CliRunner()

        # Run with --version flag
        result = runner.invoke(cli, ["--version"])

        # Should exit with zero code
        assert result.exit_code == 0, (
            f"--version should exit with code 0, got {result.exit_code}"
        )

        # Should display version information
        assert "version" in result.output.lower() or "farmer" in result.output.lower(), (
            f"Output should contain version info, got: {result.output}"
        )

    @pytest.mark.property
    def test_help_flag_exits_with_zero_code(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.5

        When the --help flag is provided, the CLI SHALL display help
        information and exit with code 0.
        """
        runner = CliRunner()

        # Run with --help flag
        result = runner.invoke(cli, ["--help"])

        # Should exit with zero code
        assert result.exit_code == 0, (
            f"--help should exit with code 0, got {result.exit_code}"
        )

        # Should display help information
        output_lower = result.output.lower()
        assert (
            "usage" in output_lower
            or "options" in output_lower
            or "commands" in output_lower
            or "help" in output_lower
        ), f"Output should contain help info, got: {result.output}"

    @pytest.mark.property
    def test_download_help_flag_exits_with_zero_code(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.5

        When the download --help flag is provided, the CLI SHALL display
        command help and exit with code 0.
        """
        runner = CliRunner()

        # Run download with --help flag
        result = runner.invoke(cli, ["download", "--help"])

        # Should exit with zero code
        assert result.exit_code == 0, (
            f"download --help should exit with code 0, got {result.exit_code}"
        )

        # Should display help information for download command
        output_lower = result.output.lower()
        assert (
            "url" in output_lower
            or "download" in output_lower
            or "format" in output_lower
            or "output" in output_lower
        ), f"Output should contain download help info, got: {result.output}"

    @given(st.text(min_size=1, max_size=10).filter(lambda x: x.strip() and not x.startswith("-")))
    @settings(max_examples=50)
    @pytest.mark.property
    def test_unknown_commands_exit_with_nonzero_code(self, unknown_command: str):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.6

        For any unknown command, the CLI SHALL exit with a non-zero code.
        """
        runner = CliRunner()

        # Skip if the command happens to be a valid one
        if unknown_command.lower() in ("download", "interactive", "help"):
            return

        # Run with an unknown command
        result = runner.invoke(cli, [unknown_command])

        # Should exit with non-zero code for unknown commands
        assert result.exit_code != 0, (
            f"Unknown command '{unknown_command}' should cause non-zero exit code, "
            f"got {result.exit_code}"
        )

    @pytest.mark.property
    def test_quiet_flag_accepted(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.4

        The --quiet flag SHALL be accepted without error.
        """
        runner = CliRunner()

        # Run with --quiet and --help (to avoid interactive mode)
        result = runner.invoke(cli, ["--quiet", "--help"])

        # Should exit with zero code (help is valid)
        assert result.exit_code == 0, (
            f"--quiet --help should exit with code 0, got {result.exit_code}"
        )

    @pytest.mark.property
    def test_short_quiet_flag_accepted(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.4

        The -q flag (short for --quiet) SHALL be accepted without error.
        """
        runner = CliRunner()

        # Run with -q and --help (to avoid interactive mode)
        result = runner.invoke(cli, ["-q", "--help"])

        # Should exit with zero code (help is valid)
        assert result.exit_code == 0, (
            f"-q --help should exit with code 0, got {result.exit_code}"
        )

    @pytest.mark.property
    def test_short_version_flag_accepted(self):
        """
        Feature: farmer-cli-completion, Property 18: CLI Invalid Argument Handling
        Validates: Requirements 13.5

        The -V flag (short for --version) SHALL be accepted without error.
        """
        runner = CliRunner()

        # Run with -V flag
        result = runner.invoke(cli, ["-V"])

        # Should exit with zero code
        assert result.exit_code == 0, (
            f"-V should exit with code 0, got {result.exit_code}"
        )

        # Should display version information
        assert "version" in result.output.lower() or "farmer" in result.output.lower(), (
            f"Output should contain version info, got: {result.output}"
        )
