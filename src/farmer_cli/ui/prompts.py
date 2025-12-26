"""
Input prompt utilities for Farmer CLI.

This module provides various input prompt functions for getting
user input with validation and styling.
"""

from typing import Callable
from typing import List
from typing import Optional

from prompt_toolkit.completion import WordCompleter
from rich.prompt import Confirm
from rich.prompt import IntPrompt
from rich.prompt import Prompt

from .console import console
from .console import get_prompt_session


def text_prompt(
    message: str,
    default: Optional[str] = None,
    password: bool = False,
    show_default: bool = True,
    validator: Optional[Callable[[str], bool]] = None,
    error_message: str = "Invalid input",
) -> str:
    """
    Prompt for text input with optional validation.

    Args:
        message: Prompt message
        default: Default value
        password: Whether to hide input
        show_default: Whether to show default value
        validator: Optional validation function
        error_message: Error message for invalid input

    Returns:
        User input string
    """
    while True:
        try:
            result = Prompt.ask(message, default=default, password=password, show_default=show_default, console=console)

            if result is None:
                result = default or ""

            if validator and not validator(result):
                console.print(f"[bold red]{error_message}[/bold red]")
                continue

            return result

        except KeyboardInterrupt:
            raise
        except Exception as e:
            console.print(f"[bold red]Input error: {e}[/bold red]")


def confirm_prompt(message: str, default: bool = False, show_default: bool = True) -> bool:
    """
    Prompt for yes/no confirmation.

    Args:
        message: Prompt message
        default: Default value
        show_default: Whether to show default

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(message, default=default, show_default=show_default, console=console)


def choice_prompt(
    message: str,
    choices: List[str],
    default: Optional[str] = None,
    show_choices: bool = True,
    case_sensitive: bool = False,
) -> str:
    """
    Prompt for a choice from a list of options.

    Args:
        message: Prompt message
        choices: List of valid choices
        default: Default choice
        show_choices: Whether to show available choices
        case_sensitive: Whether choices are case-sensitive

    Returns:
        Selected choice
    """
    result = Prompt.ask(
        message,
        choices=choices,
        default=default,
        show_choices=show_choices,
        case_sensitive=case_sensitive,
        console=console,
    )
    return result or default or ""


def int_prompt(
    message: str,
    default: Optional[int] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    show_default: bool = True,
) -> int:
    """
    Prompt for integer input.

    Args:
        message: Prompt message
        default: Default value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        show_default: Whether to show default

    Returns:
        Integer value
    """
    while True:
        try:
            result = IntPrompt.ask(message, default=default, show_default=show_default, console=console)

            if result is None:
                if default is not None:
                    return default
                continue

            if min_value is not None and result < min_value:
                console.print(f"[bold red]Value must be at least {min_value}[/bold red]")
                continue

            if max_value is not None and result > max_value:
                console.print(f"[bold red]Value must be at most {max_value}[/bold red]")
                continue

            return result

        except ValueError:
            console.print("[bold red]Please enter a valid number[/bold red]")


def password_prompt(message: str = "Password", confirmation: bool = False, min_length: int = 0) -> str:
    """
    Prompt for password input with optional confirmation.

    Args:
        message: Prompt message
        confirmation: Whether to require confirmation
        min_length: Minimum password length

    Returns:
        Password string
    """
    while True:
        password = Prompt.ask(message, password=True, console=console)

        if len(password) < min_length:
            console.print(f"[bold red]Password must be at least {min_length} characters[/bold red]")
            continue

        if confirmation:
            confirm = Prompt.ask("Confirm password", password=True, console=console)

            if password != confirm:
                console.print("[bold red]Passwords do not match[/bold red]")
                continue

        return password


def autocomplete_prompt(
    message: str, completions: List[str], default: Optional[str] = None, meta_information: Optional[dict] = None
) -> str:
    """
    Prompt with autocomplete functionality.

    Args:
        message: Prompt message
        completions: List of completion options
        default: Default value
        meta_information: Optional metadata for completions

    Returns:
        User input with autocomplete
    """
    session = get_prompt_session()
    completer = WordCompleter(completions, meta_dict=meta_information, ignore_case=True)

    return session.prompt(f"{message}: ", completer=completer, default=default or "")


def multiline_prompt(
    message: str, default: str = "", exit_message: str = "Press Ctrl+D or type ':exit' to finish"
) -> str:
    """
    Prompt for multiline text input.

    Args:
        message: Prompt message
        default: Default text
        exit_message: Message showing how to exit

    Returns:
        Multiline text
    """
    console.print(f"[bold]{message}[/bold]")
    console.print(f"[dim]{exit_message}[/dim]")

    lines = []
    session = get_prompt_session()

    try:
        if default:
            lines.append(default)

        while True:
            line = session.prompt("> ", multiline=False)
            if line.strip() == ":exit":
                break
            lines.append(line)

    except (EOFError, KeyboardInterrupt):
        pass

    return "\n".join(lines)
