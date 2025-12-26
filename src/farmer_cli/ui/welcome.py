"""
Welcome screen and visual elements for Farmer CLI.

This module provides an enhanced welcome screen with theme-aware styling.
"""

from typing import Optional
from typing import Union

from rich.align import Align
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

from themes import THEMES
from themes import VISUAL_ELEMENTS

from .console import console


def display_welcome_screen(theme: str = "default", app_name: str = "Farmer CLI", version: str = "0.2.0") -> None:
    """
    Display an enhanced welcome screen with theme-aware styling.

    Args:
        theme: Theme name to use for styling
        app_name: Application name
        version: Application version
    """
    theme_config = THEMES.get(theme, THEMES["default"])

    # Create ASCII art logo with theme styling
    logo_lines = [
        " _____ _    ____   __   __ ____  ____",
        "|  ___/ .  |  _ . |  . .  | ___||  _ .",
        "| |_ / _ . | |_) || | v | | |__ | |_) |",
        "|  _/ ___ .|  _ < | |   | | |__ |  _ <",
        "|_|/_/   ._| | |_||_|   |_|____||_| |_|",
    ]

    logo_text = Text("\n".join(logo_lines), style=theme_config["title_style"])

    # Create version and tagline
    version_text = Text(f"Version {version}", style=theme_config["subtitle_style"])
    tagline = Text("Your Terminal Companion for Digital Farming", style=theme_config["info_style"])

    # Create feature highlights
    features = [
        ("Data Processing", "Powerful data manipulation tools"),
        ("User Management", "Comprehensive user control"),
        ("Rich Themes", "Beautiful, customizable interfaces"),
        ("System Tools", "Essential utilities at your fingertips"),
    ]

    feature_panels = []
    for title, desc in features:
        feature_text = Text(f"{VISUAL_ELEMENTS['bullet']} {desc}", style=theme_config["option_style"])
        panel = Panel(
            feature_text, title=title, title_align="left", border_style=theme_config["border_style"], padding=(0, 1)
        )
        feature_panels.append(panel)

    # Create the main welcome panel
    welcome_content = Columns(
        [Align.center(logo_text, vertical="middle"), Align.center(version_text, vertical="middle")], equal=True
    )

    # Display everything
    console.clear()
    console.print()
    console.print(Align.center(welcome_content))
    console.print()
    console.print(Align.center(tagline))
    console.print()

    # Display features in a grid
    console.print(Columns(feature_panels[:2], equal=True, padding=1))
    console.print(Columns(feature_panels[2:], equal=True, padding=1))
    console.print()

    # Add navigation hint
    nav_hint = Text(
        f"{VISUAL_ELEMENTS['arrow_right']} Press Enter to continue {VISUAL_ELEMENTS['arrow_left']}",
        style=theme_config["prompt_style"],
    )
    console.print(Align.center(nav_hint))


def create_status_line(
    status: str, theme: str = "default", icon: Optional[str] = None, align: str = "left"
) -> Union[Text, Align]:
    """
    Create a themed status line with optional icon.

    Args:
        status: Status message
        theme: Theme name for styling
        icon: Optional icon from VISUAL_ELEMENTS
        align: Text alignment (left, center, right)

    Returns:
        Styled Text object
    """
    theme_config = THEMES.get(theme, THEMES["default"])

    if icon and icon in VISUAL_ELEMENTS:
        status_text = f"{VISUAL_ELEMENTS[icon]} {status}"
    else:
        status_text = status

    styled_text = Text(status_text, style=theme_config["info_style"])

    if align == "center":
        return Align.center(styled_text)
    elif align == "right":
        return Align.right(styled_text)
    else:
        return styled_text


def create_divider(
    width: int = 60, theme: str = "default", style: Optional[str] = None, text: Optional[str] = None
) -> str:
    """
    Create a themed divider line.

    Args:
        width: Width of the divider
        theme: Theme name for styling
        style: Override style (uses theme if not provided)
        text: Optional centered text in the divider

    Returns:
        Divider string
    """
    divider_char = VISUAL_ELEMENTS["horizontal_separator"]

    if text:
        # Calculate padding for centered text
        text_with_spaces = f" {text} "
        padding = (width - len(text_with_spaces)) // 2
        divider = divider_char * padding + text_with_spaces + divider_char * (width - padding - len(text_with_spaces))
    else:
        divider = divider_char * width

    return divider
