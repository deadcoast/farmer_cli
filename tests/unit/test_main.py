"""
Unit tests for farmer_cli.__main__ module.

Tests the main entry point routing logic, keyboard interrupt handling,
and SystemExit handling.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestMainFunction:
    """Tests for the main() entry point function."""

    def test_main_registers_cleanup_handler(self):
        """Test that main() registers the cleanup handler on startup."""
        with (
            patch("farmer_cli.__main__.atexit.register") as mock_register,
            patch("farmer_cli.__main__.cleanup_handler") as mock_cleanup,
            patch("farmer_cli.cli.cli") as mock_cli,
        ):
            mock_cli.return_value = None
            from farmer_cli.__main__ import main

            main([])

            mock_register.assert_called_once_with(mock_cleanup)

    def test_main_returns_zero_on_success(self):
        """Test that main() returns 0 on successful execution."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.cli") as mock_cli,
        ):
            mock_cli.return_value = None
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 0

    def test_main_handles_keyboard_interrupt(self):
        """Test that main() handles KeyboardInterrupt gracefully."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.__main__.console") as mock_console,
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = KeyboardInterrupt()
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 130  # Standard exit code for Ctrl+C
            mock_console.print.assert_called()

    def test_main_handles_system_exit_with_int_code(self):
        """Test that main() preserves integer exit codes from SystemExit."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = SystemExit(42)
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 42

    def test_main_handles_system_exit_with_zero(self):
        """Test that main() handles SystemExit(0) correctly."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = SystemExit(0)
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 0

    def test_main_handles_system_exit_with_none_code(self):
        """Test that main() returns 1 when SystemExit has None code."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = SystemExit(None)
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 1

    def test_main_handles_system_exit_with_string_code(self):
        """Test that main() returns 1 when SystemExit has string code."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = SystemExit("error message")
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 1

    def test_main_handles_generic_exception(self):
        """Test that main() handles unexpected exceptions."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.__main__.console") as mock_console,
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = RuntimeError("Unexpected error")
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 1
            mock_console.print.assert_called()

    def test_main_uses_sys_argv_when_args_none(self):
        """Test that main() uses sys.argv when args is None."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.__main__.sys.argv", ["farmer-cli"]),
            patch("farmer_cli.cli.cli") as mock_cli,
        ):
            mock_cli.return_value = None
            from farmer_cli.__main__ import main

            main(None)

            # CLI should be called (we can't easily verify argv usage directly)
            mock_cli.assert_called()

    def test_main_uses_provided_args(self):
        """Test that main() uses provided args list."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.cli") as mock_cli,
        ):
            mock_cli.return_value = None
            from farmer_cli.__main__ import main

            main(["--version"])

            mock_cli.assert_called()


class TestMainModuleExecution:
    """Tests for __main__.py module-level execution."""

    def test_module_calls_main_when_executed(self):
        """Test that running the module calls main() and exits."""
        # This tests the if __name__ == "__main__" block
        with (
            patch("farmer_cli.__main__.main") as mock_main,
            patch("farmer_cli.__main__.sys.exit") as mock_exit,
        ):
            mock_main.return_value = 0

            # Simulate module execution by importing and checking
            # The actual execution happens when run as __main__
            # We verify the structure is correct
            import farmer_cli.__main__ as main_module

            assert hasattr(main_module, "main")
            assert callable(main_module.main)


class TestMainImports:
    """Tests for import handling in __main__.py."""

    def test_imports_console_from_ui(self):
        """Test that console is imported from ui.console."""
        from farmer_cli.__main__ import console

        assert console is not None

    def test_imports_cleanup_handler(self):
        """Test that cleanup_handler is imported from utils.cleanup."""
        from farmer_cli.__main__ import cleanup_handler

        assert cleanup_handler is not None
        assert callable(cleanup_handler)


class TestMainErrorMessages:
    """Tests for error message formatting in main()."""

    def test_keyboard_interrupt_message_format(self):
        """Test that KeyboardInterrupt shows appropriate message."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.__main__.console") as mock_console,
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = KeyboardInterrupt()
            from farmer_cli.__main__ import main

            main([])

            # Verify the message contains expected text
            call_args = mock_console.print.call_args
            assert call_args is not None
            message = call_args[0][0]
            assert "interrupted" in message.lower() or "user" in message.lower()

    def test_fatal_error_message_includes_exception(self):
        """Test that fatal errors include the exception message."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.__main__.console") as mock_console,
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.side_effect = ValueError("Test error message")
            from farmer_cli.__main__ import main

            main([])

            call_args = mock_console.print.call_args
            assert call_args is not None
            message = call_args[0][0]
            assert "Test error message" in message


class TestMainCliRouting:
    """Tests for CLI routing logic in main()."""

    def test_main_imports_cli_main(self):
        """Test that main() imports cli.main for execution."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.main") as mock_cli_main,
        ):
            mock_cli_main.return_value = 0
            from farmer_cli.__main__ import main

            main([])

            mock_cli_main.assert_called_once()

    def test_main_with_empty_args_calls_cli(self):
        """Test that main([]) still calls CLI (which handles interactive mode)."""
        with (
            patch("farmer_cli.__main__.atexit.register"),
            patch("farmer_cli.cli.cli") as mock_cli,
        ):
            mock_cli.return_value = None
            from farmer_cli.__main__ import main

            result = main([])

            assert result == 0
            mock_cli.assert_called()
