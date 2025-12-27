"""
Unit tests for farmer_cli.ui.menu module.

Tests the MenuManager class including main menu display, submenu display,
and menu stack operations.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestMenuManagerInit:
    """Tests for MenuManager initialization."""

    def test_initializes_empty_menu_stack(self):
        """Test that MenuManager initializes with empty menu stack."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        assert manager.menu_stack == []

    def test_menu_stack_is_list(self):
        """Test that menu_stack is a list."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        assert isinstance(manager.menu_stack, list)


class TestDisplayMainMenu:
    """Tests for MenuManager.display_main_menu method."""

    def test_returns_valid_choice(self):
        """Test that valid choice is returned."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch("farmer_cli.ui.menu.MENU_OPTIONS", ["Option 1", "Option 2", "Exit"]),
        ):
            mock_prompt.ask.return_value = "1"

            result = manager.display_main_menu()

            assert result == "1"

    def test_returns_none_for_invalid_choice(self):
        """Test that invalid choice returns None."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch("farmer_cli.ui.menu.MENU_OPTIONS", ["Option 1", "Exit"]),
        ):
            mock_prompt.ask.return_value = "99"
            mock_console.input.return_value = ""

            result = manager.display_main_menu()

            assert result is None

    def test_help_command_returns_none(self):
        """Test that 'help' command displays help and returns None."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch.object(manager, "_display_help") as mock_help,
        ):
            mock_prompt.ask.return_value = "help"

            result = manager.display_main_menu()

            assert result is None
            mock_help.assert_called_once()

    def test_help_case_insensitive(self):
        """Test that 'HELP' command is case insensitive."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch.object(manager, "_display_help") as mock_help,
        ):
            mock_prompt.ask.return_value = "HELP"

            result = manager.display_main_menu()

            assert result is None
            mock_help.assert_called_once()

    def test_clears_console(self):
        """Test that console is cleared before displaying menu."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch("farmer_cli.ui.menu.MENU_OPTIONS", ["Exit"]),
        ):
            mock_prompt.ask.return_value = "0"

            manager.display_main_menu()

            mock_console.clear.assert_called_once()

    def test_uses_theme_parameter(self):
        """Test that theme parameter is used."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame") as mock_frame,
            patch("farmer_cli.ui.menu.MENU_OPTIONS", ["Exit"]),
            patch("farmer_cli.ui.menu.THEMES", {"custom": {"border_style": "blue"}, "default": {"border_style": "white"}}),
        ):
            mock_prompt.ask.return_value = "0"

            manager.display_main_menu(theme="custom")

            # Verify create_frame was called with theme
            call_kwargs = mock_frame.call_args[1]
            assert call_kwargs["theme"] == "custom"

    def test_exit_choice_zero(self):
        """Test that choice '0' is valid for exit."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
            patch("farmer_cli.ui.widgets.display_greeting"),
            patch("farmer_cli.ui.menu.create_frame"),
            patch("farmer_cli.ui.menu.MENU_OPTIONS", ["Option 1", "Exit"]),
        ):
            mock_prompt.ask.return_value = "0"

            result = manager.display_main_menu()

            assert result == "0"


class TestDisplaySubmenu:
    """Tests for MenuManager.display_submenu method."""

    def test_returns_valid_choice(self):
        """Test that valid choice is returned."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("1", "Option 1"), ("2", "Option 2"), ("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "1"

            result = manager.display_submenu("Test Menu", options)

            assert result == "1"

    def test_returns_none_for_back_choice(self):
        """Test that '0' choice returns None (back to main menu)."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("1", "Option 1"), ("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "0"

            result = manager.display_submenu("Test Menu", options)

            assert result is None

    def test_clears_console(self):
        """Test that console is cleared before displaying submenu."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "0"

            manager.display_submenu("Test Menu", options)

            mock_console.clear.assert_called_once()

    def test_displays_title(self):
        """Test that submenu title is displayed."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "0"

            manager.display_submenu("Custom Title", options)

            # Check that title was printed
            calls = mock_console.print.call_args_list
            title_printed = any("Custom Title" in str(call) for call in calls)
            assert title_printed

    def test_displays_all_options(self):
        """Test that all options are displayed."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("1", "First Option"), ("2", "Second Option"), ("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "0"

            manager.display_submenu("Menu", options)

            # Check that options were printed
            calls = mock_console.print.call_args_list
            assert len(calls) >= 3  # Title + at least 3 options

    def test_uses_valid_choices_for_prompt(self):
        """Test that Prompt.ask receives valid choices."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        options = [("a", "Option A"), ("b", "Option B"), ("0", "Back")]

        with (
            patch("farmer_cli.ui.menu.console"),
            patch("farmer_cli.ui.menu.Prompt") as mock_prompt,
        ):
            mock_prompt.ask.return_value = "a"

            manager.display_submenu("Menu", options)

            call_kwargs = mock_prompt.ask.call_args[1]
            assert set(call_kwargs["choices"]) == {"a", "b", "0"}


class TestDisplayHelp:
    """Tests for MenuManager._display_help method."""

    def test_calls_display_quick_help(self):
        """Test that _display_help calls display_quick_help."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.features.help_system.display_quick_help") as mock_help,
        ):
            mock_console.input.return_value = ""

            manager._display_help()

            mock_help.assert_called_once()

    def test_waits_for_user_input(self):
        """Test that _display_help waits for user to press Enter."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        with (
            patch("farmer_cli.ui.menu.console") as mock_console,
            patch("farmer_cli.features.help_system.display_quick_help"),
        ):
            mock_console.input.return_value = ""

            manager._display_help()

            mock_console.input.assert_called_once()


class TestPushMenu:
    """Tests for MenuManager.push_menu method."""

    def test_pushes_menu_to_stack(self):
        """Test that push_menu adds menu to stack."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        manager.push_menu("submenu1")

        assert manager.menu_stack == ["submenu1"]

    def test_pushes_multiple_menus(self):
        """Test that multiple menus can be pushed."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        manager.push_menu("menu1")
        manager.push_menu("menu2")
        manager.push_menu("menu3")

        assert manager.menu_stack == ["menu1", "menu2", "menu3"]

    def test_preserves_order(self):
        """Test that push order is preserved (LIFO)."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        manager.push_menu("first")
        manager.push_menu("second")

        assert manager.menu_stack[-1] == "second"


class TestPopMenu:
    """Tests for MenuManager.pop_menu method."""

    def test_pops_last_menu(self):
        """Test that pop_menu returns last pushed menu."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        manager.push_menu("menu1")
        manager.push_menu("menu2")

        result = manager.pop_menu()

        assert result == "menu2"

    def test_removes_from_stack(self):
        """Test that pop_menu removes menu from stack."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        manager.push_menu("menu1")
        manager.push_menu("menu2")

        manager.pop_menu()

        assert manager.menu_stack == ["menu1"]

    def test_returns_none_for_empty_stack(self):
        """Test that pop_menu returns None for empty stack."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        result = manager.pop_menu()

        assert result is None

    def test_multiple_pops(self):
        """Test that multiple pops work correctly."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        manager.push_menu("menu1")
        manager.push_menu("menu2")

        first_pop = manager.pop_menu()
        second_pop = manager.pop_menu()
        third_pop = manager.pop_menu()

        assert first_pop == "menu2"
        assert second_pop == "menu1"
        assert third_pop is None


class TestClearStack:
    """Tests for MenuManager.clear_stack method."""

    def test_clears_all_menus(self):
        """Test that clear_stack removes all menus."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        manager.push_menu("menu1")
        manager.push_menu("menu2")
        manager.push_menu("menu3")

        manager.clear_stack()

        assert manager.menu_stack == []

    def test_clear_empty_stack(self):
        """Test that clearing empty stack doesn't error."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()

        manager.clear_stack()  # Should not raise

        assert manager.menu_stack == []

    def test_stack_usable_after_clear(self):
        """Test that stack can be used after clearing."""
        from farmer_cli.ui.menu import MenuManager

        manager = MenuManager()
        manager.push_menu("old_menu")
        manager.clear_stack()

        manager.push_menu("new_menu")

        assert manager.menu_stack == ["new_menu"]
