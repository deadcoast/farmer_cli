"""
Unit tests for farmer_cli.ui.prompts module.

Tests the input prompt utilities including text, confirm, choice,
integer, password, autocomplete, and multiline prompts.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestTextPrompt:
    """Tests for text_prompt function."""

    def test_returns_user_input(self):
        """Test that text_prompt returns user input."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "test input"

            result = text_prompt("Enter text")

            assert result == "test input"

    def test_uses_default_when_provided(self):
        """Test that default value is passed to Prompt.ask."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "default value"

            result = text_prompt("Enter text", default="default value")

            mock_prompt.ask.assert_called_once()
            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["default"] == "default value"

    def test_password_mode(self):
        """Test that password mode hides input."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "secret"

            text_prompt("Password", password=True)

            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["password"] is True

    def test_validator_accepts_valid_input(self):
        """Test that validator accepts valid input."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "valid"

            result = text_prompt("Enter text", validator=lambda x: len(x) > 0)

            assert result == "valid"

    def test_validator_rejects_invalid_input(self):
        """Test that validator rejects invalid input and reprompts."""
        from farmer_cli.ui.prompts import text_prompt

        with (
            patch("farmer_cli.ui.prompts.Prompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            # First call returns invalid, second returns valid
            mock_prompt.ask.side_effect = ["", "valid"]

            result = text_prompt("Enter text", validator=lambda x: len(x) > 0)

            assert result == "valid"
            assert mock_prompt.ask.call_count == 2
            mock_console.print.assert_called()

    def test_custom_error_message(self):
        """Test that custom error message is displayed."""
        from farmer_cli.ui.prompts import text_prompt

        with (
            patch("farmer_cli.ui.prompts.Prompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            mock_prompt.ask.side_effect = ["", "valid"]

            text_prompt("Enter text", validator=lambda x: len(x) > 0, error_message="Cannot be empty")

            # Check error message was printed
            call_args = mock_console.print.call_args[0][0]
            assert "Cannot be empty" in call_args

    def test_keyboard_interrupt_propagates(self):
        """Test that KeyboardInterrupt is propagated."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = KeyboardInterrupt()

            with pytest.raises(KeyboardInterrupt):
                text_prompt("Enter text")

    def test_returns_default_when_result_none(self):
        """Test that default is returned when result is None."""
        from farmer_cli.ui.prompts import text_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = None

            result = text_prompt("Enter text", default="fallback")

            assert result == "fallback"


class TestConfirmPrompt:
    """Tests for confirm_prompt function."""

    def test_returns_true_on_yes(self):
        """Test that confirm_prompt returns True on yes."""
        from farmer_cli.ui.prompts import confirm_prompt

        with patch("farmer_cli.ui.prompts.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = True

            result = confirm_prompt("Continue?")

            assert result is True

    def test_returns_false_on_no(self):
        """Test that confirm_prompt returns False on no."""
        from farmer_cli.ui.prompts import confirm_prompt

        with patch("farmer_cli.ui.prompts.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False

            result = confirm_prompt("Continue?")

            assert result is False

    def test_uses_default_value(self):
        """Test that default value is passed correctly."""
        from farmer_cli.ui.prompts import confirm_prompt

        with patch("farmer_cli.ui.prompts.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = True

            confirm_prompt("Continue?", default=True)

            call_kwargs = mock_confirm.ask.call_args[1]
            assert call_kwargs["default"] is True

    def test_show_default_option(self):
        """Test that show_default option is passed."""
        from farmer_cli.ui.prompts import confirm_prompt

        with patch("farmer_cli.ui.prompts.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False

            confirm_prompt("Continue?", show_default=False)

            call_kwargs = mock_confirm.ask.call_args[1]
            assert call_kwargs["show_default"] is False


class TestChoicePrompt:
    """Tests for choice_prompt function."""

    def test_returns_selected_choice(self):
        """Test that choice_prompt returns selected choice."""
        from farmer_cli.ui.prompts import choice_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "option2"

            result = choice_prompt("Select", choices=["option1", "option2", "option3"])

            assert result == "option2"

    def test_uses_default_choice(self):
        """Test that default choice is passed correctly."""
        from farmer_cli.ui.prompts import choice_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "default"

            choice_prompt("Select", choices=["a", "b", "default"], default="default")

            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["default"] == "default"

    def test_show_choices_option(self):
        """Test that show_choices option is passed."""
        from farmer_cli.ui.prompts import choice_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "a"

            choice_prompt("Select", choices=["a", "b"], show_choices=False)

            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["show_choices"] is False

    def test_case_sensitive_option(self):
        """Test that case_sensitive option is passed."""
        from farmer_cli.ui.prompts import choice_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "A"

            choice_prompt("Select", choices=["A", "B"], case_sensitive=True)

            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["case_sensitive"] is True

    def test_returns_default_when_result_none(self):
        """Test that default is returned when result is None."""
        from farmer_cli.ui.prompts import choice_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = None

            result = choice_prompt("Select", choices=["a", "b"], default="a")

            assert result == "a"


class TestIntPrompt:
    """Tests for int_prompt function."""

    def test_returns_integer_input(self):
        """Test that int_prompt returns integer input."""
        from farmer_cli.ui.prompts import int_prompt

        with patch("farmer_cli.ui.prompts.IntPrompt") as mock_prompt:
            mock_prompt.ask.return_value = 42

            result = int_prompt("Enter number")

            assert result == 42

    def test_uses_default_value(self):
        """Test that default value is used when result is None."""
        from farmer_cli.ui.prompts import int_prompt

        with patch("farmer_cli.ui.prompts.IntPrompt") as mock_prompt:
            mock_prompt.ask.return_value = None

            result = int_prompt("Enter number", default=10)

            assert result == 10

    def test_min_value_validation(self):
        """Test that min_value validation works."""
        from farmer_cli.ui.prompts import int_prompt

        with (
            patch("farmer_cli.ui.prompts.IntPrompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            # First call returns too low, second returns valid
            mock_prompt.ask.side_effect = [3, 10]

            result = int_prompt("Enter number", min_value=5)

            assert result == 10
            assert mock_prompt.ask.call_count == 2
            mock_console.print.assert_called()

    def test_max_value_validation(self):
        """Test that max_value validation works."""
        from farmer_cli.ui.prompts import int_prompt

        with (
            patch("farmer_cli.ui.prompts.IntPrompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            # First call returns too high, second returns valid
            mock_prompt.ask.side_effect = [100, 50]

            result = int_prompt("Enter number", max_value=75)

            assert result == 50
            assert mock_prompt.ask.call_count == 2

    def test_min_and_max_validation(self):
        """Test that both min and max validation work together."""
        from farmer_cli.ui.prompts import int_prompt

        with (
            patch("farmer_cli.ui.prompts.IntPrompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console"),
        ):
            # First too low, second too high, third valid
            mock_prompt.ask.side_effect = [1, 100, 50]

            result = int_prompt("Enter number", min_value=10, max_value=90)

            assert result == 50
            assert mock_prompt.ask.call_count == 3


class TestPasswordPrompt:
    """Tests for password_prompt function."""

    def test_returns_password(self):
        """Test that password_prompt returns password."""
        from farmer_cli.ui.prompts import password_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "secret123"

            result = password_prompt("Password")

            assert result == "secret123"

    def test_password_mode_enabled(self):
        """Test that password mode is enabled."""
        from farmer_cli.ui.prompts import password_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "secret"

            password_prompt()

            call_kwargs = mock_prompt.ask.call_args[1]
            assert call_kwargs["password"] is True

    def test_min_length_validation(self):
        """Test that min_length validation works."""
        from farmer_cli.ui.prompts import password_prompt

        with (
            patch("farmer_cli.ui.prompts.Prompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            # First too short, second valid
            mock_prompt.ask.side_effect = ["abc", "validpassword"]

            result = password_prompt(min_length=8)

            assert result == "validpassword"
            assert mock_prompt.ask.call_count == 2
            mock_console.print.assert_called()

    def test_confirmation_matching(self):
        """Test that confirmation must match."""
        from farmer_cli.ui.prompts import password_prompt

        with patch("farmer_cli.ui.prompts.Prompt") as mock_prompt:
            # Password, wrong confirm, password again, correct confirm
            mock_prompt.ask.side_effect = ["password1", "wrong", "password2", "password2"]

            result = password_prompt(confirmation=True)

            assert result == "password2"

    def test_confirmation_mismatch_reprompts(self):
        """Test that mismatched confirmation reprompts."""
        from farmer_cli.ui.prompts import password_prompt

        with (
            patch("farmer_cli.ui.prompts.Prompt") as mock_prompt,
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            mock_prompt.ask.side_effect = ["pass1", "pass2", "pass3", "pass3"]

            password_prompt(confirmation=True)

            # Should show mismatch error
            assert mock_console.print.call_count >= 1


class TestAutocompletePrompt:
    """Tests for autocomplete_prompt function."""

    def test_returns_user_input(self):
        """Test that autocomplete_prompt returns user input."""
        from farmer_cli.ui.prompts import autocomplete_prompt

        mock_session = MagicMock()
        mock_session.prompt.return_value = "selected"

        with patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session):
            result = autocomplete_prompt("Select", completions=["a", "b", "c"])

            assert result == "selected"

    def test_uses_completions(self):
        """Test that completions are passed to WordCompleter."""
        from farmer_cli.ui.prompts import autocomplete_prompt

        mock_session = MagicMock()
        mock_session.prompt.return_value = "test"

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.WordCompleter") as mock_completer,
        ):
            autocomplete_prompt("Select", completions=["opt1", "opt2"])

            mock_completer.assert_called_once()
            call_args = mock_completer.call_args[0]
            assert call_args[0] == ["opt1", "opt2"]

    def test_uses_default_value(self):
        """Test that default value is passed to prompt."""
        from farmer_cli.ui.prompts import autocomplete_prompt

        mock_session = MagicMock()
        mock_session.prompt.return_value = "default"

        with patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session):
            autocomplete_prompt("Select", completions=["a"], default="default")

            call_kwargs = mock_session.prompt.call_args[1]
            assert call_kwargs["default"] == "default"

    def test_meta_information_passed(self):
        """Test that meta_information is passed to WordCompleter."""
        from farmer_cli.ui.prompts import autocomplete_prompt

        mock_session = MagicMock()
        mock_session.prompt.return_value = "test"
        meta = {"opt1": "Description 1"}

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.WordCompleter") as mock_completer,
        ):
            autocomplete_prompt("Select", completions=["opt1"], meta_information=meta)

            call_kwargs = mock_completer.call_args[1]
            assert call_kwargs["meta_dict"] == meta


class TestMultilinePrompt:
    """Tests for multiline_prompt function."""

    def test_returns_multiline_text(self):
        """Test that multiline_prompt returns joined lines."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["line1", "line2", ":exit"]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console"),
        ):
            result = multiline_prompt("Enter text")

            assert "line1" in result
            assert "line2" in result

    def test_exit_command_stops_input(self):
        """Test that :exit command stops input."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["line1", ":exit"]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console"),
        ):
            result = multiline_prompt("Enter text")

            assert result == "line1"

    def test_eof_stops_input(self):
        """Test that EOFError (Ctrl+D) stops input."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["line1", EOFError()]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console"),
        ):
            result = multiline_prompt("Enter text")

            assert result == "line1"

    def test_keyboard_interrupt_stops_input(self):
        """Test that KeyboardInterrupt stops input."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["line1", KeyboardInterrupt()]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console"),
        ):
            result = multiline_prompt("Enter text")

            assert result == "line1"

    def test_default_text_included(self):
        """Test that default text is included in result."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["line2", ":exit"]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console"),
        ):
            result = multiline_prompt("Enter text", default="line1")

            assert "line1" in result
            assert "line2" in result

    def test_displays_message_and_exit_hint(self):
        """Test that message and exit hint are displayed."""
        from farmer_cli.ui.prompts import multiline_prompt

        mock_session = MagicMock()
        mock_session.prompt.side_effect = [":exit"]

        with (
            patch("farmer_cli.ui.prompts.get_prompt_session", return_value=mock_session),
            patch("farmer_cli.ui.prompts.console") as mock_console,
        ):
            multiline_prompt("Enter text", exit_message="Custom exit message")

            # Should print message and exit hint
            assert mock_console.print.call_count >= 2
