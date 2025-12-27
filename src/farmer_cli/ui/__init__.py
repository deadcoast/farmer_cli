"""
User Interface components for Farmer CLI.

This module provides all UI components including console setup,
menu systems, widgets, layouts, and input prompts.
"""

from .console import console
from .console import setup_console
from .download_ui import create_download_progress
from .download_ui import display_download_history
from .download_ui import display_download_queue
from .layouts import create_main_layout
from .menu import MenuManager
from .prompts import choice_prompt
from .prompts import confirm_prompt
from .prompts import password_prompt
from .prompts import text_prompt
from .widgets import create_frame
from .widgets import create_table
from .widgets import display_greeting
from .widgets import show_progress


__all__ = [
    # Menu
    "MenuManager",
    # Prompts
    "choice_prompt",
    "confirm_prompt",
    # Console
    "console",
    # Widgets
    "create_download_progress",
    "create_frame",
    "create_main_layout",
    "create_table",
    "display_download_history",
    "display_download_queue",
    "display_greeting",
    "password_prompt",
    "setup_console",
    "show_progress",
    "text_prompt",
]
