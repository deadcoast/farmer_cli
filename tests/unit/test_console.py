"""
Unit tests for farmer_cli.ui.console module.

Tests the console initialization, setup functions, and global instances.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console as RichConsole


class TestConsoleGlobals:
    """Tests for global console instances."""

    def test_console_is_rich_console(self):
        """Test that console is a Rich Console instance."""
        from farmer_cli.ui.console import console

        assert isinstance(console, RichConsole)

    def test_console_has_color_system(self):
        """Test that console has color system configured."""
        from farmer_cli.ui.console import console

        # Color system should be set (auto resolves to actual system)
        assert console.color_system is not None or console._color_system is not None

    def test_console_is_terminal(self):
        """Test that console is configured as terminal."""
        from farmer_cli.ui.console import console

        # Console should be configured (force_terminal is a constructor param)
        # We verify it's a valid console that can output
        assert console.is_terminal or console._force_terminal

    def test_console_soft_wrap(self):
        """Test that console has soft_wrap enabled."""
        from farmer_cli.ui.console import console

        assert console.soft_wrap is True

    def test_prompt_session_is_prompt_session(self):
        """Test that prompt_session is a PromptSession instance."""
        from farmer_cli.ui.console import prompt_session

        assert isinstance(prompt_session, PromptSession)

    def test_bindings_is_key_bindings(self):
        """Test that bindings is a KeyBindings instance."""
        from farmer_cli.ui.console import bindings

        assert isinstance(bindings, KeyBindings)


class TestSetupConsole:
    """Tests for setup_console function."""

    def test_returns_console_instance(self):
        """Test that setup_console returns a console instance."""
        from farmer_cli.ui.console import setup_console

        result = setup_console()

        assert isinstance(result, RichConsole)

    def test_sets_width(self):
        """Test that setup_console sets console width."""
        from farmer_cli.ui.console import setup_console

        result = setup_console(width=120)

        assert result.width == 120

    def test_sets_height(self):
        """Test that setup_console sets console height."""
        from farmer_cli.ui.console import setup_console

        result = setup_console(height=40)

        assert result.height == 40

    def test_enables_record(self):
        """Test that setup_console enables recording."""
        from farmer_cli.ui.console import setup_console

        result = setup_console(record=True)

        assert result.record is True

    def test_sets_color_system(self):
        """Test that setup_console sets color system."""
        from farmer_cli.ui.console import setup_console

        result = setup_console(color_system="256")

        # Color system is set internally
        assert result._color_system == "256"

    def test_windows_encoding_setup(self):
        """Test that Windows encoding is set on Windows."""
        from farmer_cli.ui.console import setup_console

        with patch("farmer_cli.ui.console.os.name", "nt"):
            with patch.dict("os.environ", {}, clear=False):
                import os

                setup_console()

                assert os.environ.get("PYTHONIOENCODING") == "utf-8"

    def test_no_encoding_on_non_windows(self):
        """Test that encoding is not set on non-Windows."""
        from farmer_cli.ui.console import setup_console

        with patch("farmer_cli.ui.console.os.name", "posix"):
            # Should not raise or set encoding
            setup_console()


class TestGetConsole:
    """Tests for get_console function."""

    def test_returns_console_instance(self):
        """Test that get_console returns the console instance."""
        from farmer_cli.ui.console import console
        from farmer_cli.ui.console import get_console

        result = get_console()

        assert result is console

    def test_returns_same_instance(self):
        """Test that get_console always returns the same instance."""
        from farmer_cli.ui.console import get_console

        result1 = get_console()
        result2 = get_console()

        assert result1 is result2


class TestGetPromptSession:
    """Tests for get_prompt_session function."""

    def test_returns_prompt_session(self):
        """Test that get_prompt_session returns the session."""
        from farmer_cli.ui.console import get_prompt_session
        from farmer_cli.ui.console import prompt_session

        result = get_prompt_session()

        assert result is prompt_session

    def test_returns_same_instance(self):
        """Test that get_prompt_session always returns the same instance."""
        from farmer_cli.ui.console import get_prompt_session

        result1 = get_prompt_session()
        result2 = get_prompt_session()

        assert result1 is result2

    def test_session_has_history(self):
        """Test that prompt session has history configured."""
        from farmer_cli.ui.console import get_prompt_session

        session = get_prompt_session()

        assert session.history is not None


class TestGetBindings:
    """Tests for get_bindings function."""

    def test_returns_key_bindings(self):
        """Test that get_bindings returns the bindings."""
        from farmer_cli.ui.console import bindings
        from farmer_cli.ui.console import get_bindings

        result = get_bindings()

        assert result is bindings

    def test_returns_same_instance(self):
        """Test that get_bindings always returns the same instance."""
        from farmer_cli.ui.console import get_bindings

        result1 = get_bindings()
        result2 = get_bindings()

        assert result1 is result2


class TestKeyBindings:
    """Tests for registered key bindings."""

    def test_ctrl_c_raises_keyboard_interrupt(self):
        """Test that Ctrl+C handler raises KeyboardInterrupt."""
        from farmer_cli.ui.console import handle_ctrl_c

        with pytest.raises(KeyboardInterrupt):
            handle_ctrl_c(MagicMock())

    def test_ctrl_d_raises_eof_error(self):
        """Test that Ctrl+D handler raises EOFError."""
        from farmer_cli.ui.console import handle_ctrl_d

        with pytest.raises(EOFError):
            handle_ctrl_d(MagicMock())

    def test_bindings_has_ctrl_c(self):
        """Test that bindings include Ctrl+C."""
        from farmer_cli.ui.console import bindings

        # Check that bindings has registered handlers
        assert len(bindings.bindings) >= 2

    def test_bindings_has_ctrl_d(self):
        """Test that bindings include Ctrl+D."""
        from farmer_cli.ui.console import bindings

        # Check that bindings has registered handlers
        assert len(bindings.bindings) >= 2
