"""
Console setup and configuration.

This module provides the Rich console instance and configuration
functions for the Farmer CLI application.
"""

import os
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console as RichConsole


# Global console instance
console = RichConsole(color_system="auto", force_terminal=True, force_jupyter=False, soft_wrap=True)

# Global prompt session
prompt_session = PromptSession(history=InMemoryHistory())  # type: ignore

# Global key bindings
bindings = KeyBindings()


def setup_console(
    color_system: Optional[str] = None, width: Optional[int] = None, height: Optional[int] = None, record: bool = False
) -> RichConsole:
    """
    Setup and configure the console.

    Args:
        color_system: Color system to use ("auto", "standard", "256", "truecolor", "windows")
        width: Console width (defaults to terminal width)
        height: Console height (defaults to terminal height)
        record: Whether to record console output

    Returns:
        Configured console instance
    """
    global console

    # Update console configuration
    if color_system:
        console._color_system = color_system  # type: ignore[assignment]

    if width:
        console.width = width

    if height:
        console.height = height

    if record:
        console.record = True

    # Set environment for better terminal compatibility
    if os.name == "nt":  # Windows
        os.environ["PYTHONIOENCODING"] = "utf-8"

    return console


def get_console() -> RichConsole:
    """
    Get the global console instance.

    Returns:
        The Rich console instance
    """
    return console


def get_prompt_session() -> PromptSession:
    """
    Get the global prompt session.

    Returns:
        The PromptSession instance
    """
    return prompt_session


def get_bindings() -> KeyBindings:
    """
    Get the global key bindings.

    Returns:
        The KeyBindings instance
    """
    return bindings


# Register default key bindings
@bindings.add("c-c")
def handle_ctrl_c(event):
    """Handle Ctrl+C to exit."""
    raise KeyboardInterrupt()


@bindings.add("c-d")
def handle_ctrl_d(event):
    """Handle Ctrl+D to exit."""
    raise EOFError()
