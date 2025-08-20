"""
Theme definitions for the Farmer CLI application.

This module contains all UI theme configurations for Rich styling.
"""

from typing import Dict


# Border character sets
SINGLE_LINE: Dict[str, str] = {
    "top_left": "┌",
    "top_right": "┐",
    "bottom_left": "└",
    "bottom_right": "┘",
    "horizontal": "─",
    "vertical": "│",
    "cross": "┼",
}

DOUBLE_LINE: Dict[str, str] = {
    "top_left": "╔",
    "top_right": "╗",
    "bottom_left": "╚",
    "bottom_right": "╝",
    "horizontal": "═",
    "vertical": "║",
    "cross": "╬",
}

# Theme definitions
THEMES: Dict[str, Dict[str, str]] = {
    "default": {
        "border_style": "bold magenta",
        "title_style": "bold cyan",
        "option_style": "bold white",
        "highlight_style": "bold yellow",
        "success_style": "bold green",
        "error_style": "bold red",
        "warning_style": "bold yellow",
        "info_style": "bold blue",
    },
    "dark": {
        "border_style": "bold white",
        "title_style": "bold green",
        "option_style": "bold white",
        "highlight_style": "bold red",
        "success_style": "bold green",
        "error_style": "bold red",
        "warning_style": "bold yellow",
        "info_style": "bold cyan",
    },
    "light": {
        "border_style": "bold black",
        "title_style": "bold blue",
        "option_style": "bold black",
        "highlight_style": "bold blue",
        "success_style": "bold green",
        "error_style": "bold red",
        "warning_style": "bold yellow",
        "info_style": "bold blue",
    },
    "high_contrast": {
        "border_style": "bold white",
        "title_style": "bold yellow",
        "option_style": "bold white",
        "highlight_style": "bold cyan",
        "success_style": "bold green",
        "error_style": "bold red",
        "warning_style": "bold yellow",
        "info_style": "bold white",
    },
}

# Help text definitions
HELP_TEXTS: Dict[str, str] = {
    "1": "Option One allows you to perform action X.",
    "2": "Option Two helps you manage Y.",
    "3": "Option Three is used for configuring Z.",
    "4": "Option Four enables you to monitor A.",
    "0": "Exit the application.",
}
