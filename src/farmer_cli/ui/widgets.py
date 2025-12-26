"""
UI widgets for Farmer CLI.

This module provides reusable UI components like frames, tables,
progress bars, and other visual elements.
"""

from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from rich.align import Align
from rich.live import Live
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.table import Table
from rich.text import Text

from themes import DOUBLE_LINE
from themes import THEMES
from themes import VISUAL_ELEMENTS

from .console import console


def create_frame(
    content: str,
    width: int = 60,
    border_style: str = "bold magenta",
    padding: int = 2,
    border_chars: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    theme: Optional[str] = None,
) -> Text:
    """
    Create a framed text with the specified content and style.

    Args:
        content: The inner content of the frame
        width: The total width of the frame
        border_style: The style/color of the border
        padding: Internal padding (spaces on each side)
        border_chars: Custom border character set (defaults to DOUBLE_LINE)
        title: Optional title to display in the top border
        theme: Theme name to use for styling

    Returns:
        A Rich Text object with a custom frame
    """
    # Use theme if provided
    if theme and theme in THEMES:
        theme_config = THEMES[theme]
        border_style = theme_config.get("border_style", border_style)
        border_chars = border_chars or theme_config.get("border_chars", DOUBLE_LINE)
    else:
        border_chars = border_chars or DOUBLE_LINE

    # Get border characters
    tl = border_chars["top_left"]
    tr = border_chars["top_right"]
    bl = border_chars["bottom_left"]
    br = border_chars["bottom_right"]
    h = border_chars["horizontal"]
    v = border_chars["vertical"]

    # Build the top border with optional title
    if title:
        # Ensure title fits within the border
        max_title_len = width - 6  # Leave space for corners and spacing
        if len(title) > max_title_len:
            title = title[: max_title_len - 3] + "..."

        # Calculate padding for centered title
        title_with_spaces = f" {title} "
        padding_total = width - 2 - len(title_with_spaces)
        padding_left = padding_total // 2
        padding_right = padding_total - padding_left

        top_border = f"{tl}{h * padding_left}{title_with_spaces}{h * padding_right}{tr}"
    else:
        top_border = f"{tl}{h * (width - 2)}{tr}"

    # Split content into lines
    content_lines = content.split("\n")

    # Build the middle content with borders
    middle = ""
    padding_str = " " * padding
    content_width = width - (padding * 2) - 2  # Account for borders and padding

    for line in content_lines:
        # Remove any markup from the line for proper display in frame
        clean_line = Text.from_markup(line.strip()).plain if "[" in line else line.strip()
        # Truncate and pad the line to fit the width
        padded_line = clean_line[:content_width].ljust(content_width)
        middle += f"{v}{padding_str}{padded_line}{padding_str}{v}\n"

    # Build the bottom border
    bottom_border = f"{bl}{h * (width - 2)}{br}"

    # Combine all parts
    full_frame = f"{top_border}\n{middle}{bottom_border}"

    return Text(full_frame, style=border_style)


def create_table(
    title: str,
    columns: List[Tuple[str, Dict[str, Any]]],
    rows: List[List[Any]],
    show_header: bool = True,
    show_lines: bool = False,
    style: str = "bold blue",
) -> Table:
    """
    Create a formatted table.

    Args:
        title: Table title
        columns: List of (column_name, column_kwargs) tuples
        rows: List of row data
        show_header: Whether to show column headers
        show_lines: Whether to show row lines
        style: Table style

    Returns:
        Rich Table object
    """
    table = Table(title=title, style=style, show_header=show_header, show_lines=show_lines)

    # Add columns
    for col_name, col_kwargs in columns:
        table.add_column(col_name, **col_kwargs)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def display_greeting(app_name: str, version: str) -> None:
    """
    Display the welcome greeting.

    Args:
        app_name: Application name
        version: Application version
    """
    greeting = f"Welcome to {app_name} v{version}\nPlease see options below..."
    styled_greeting = Text(greeting, style="bold green")
    console.print(Align.center(styled_greeting, vertical="top"))


def show_progress(
    description: str = "Processing...", total: Optional[int] = None, auto_refresh: bool = True
) -> Progress:
    """
    Create and return a progress bar.

    Args:
        description: Progress description
        total: Total steps (None for indeterminate)
        auto_refresh: Whether to auto-refresh

    Returns:
        Progress object

    Example:
        with show_progress("Loading...", 100) as progress:
            task = progress.add_task("Processing", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        auto_refresh=auto_refresh,
    )


def animate_text(text: str, style: str = "bold green", delay: float = 0.05) -> None:
    """
    Animate text display character by character.

    Args:
        text: Text to animate
        style: Text style
        delay: Delay between characters
    """
    styled_text = Text(style=style)

    with Live(styled_text, console=console, refresh_per_second=20) as live:
        for char in text:
            styled_text.append(char)
            live.update(styled_text)
            sleep(delay)


def display_logo() -> None:
    """Display the application logo."""
    logo = r"""
  ____  _    ____  __  __ _____ ____
 | ___|/ \  |  _ \|  \/  | ____|  _ \
 | __|/ _ \ | |_) | |\/| |  _| | |_) |
 | | / ___ \|  _ <| |  | | |___|  _ <
 |_|/_/   \_\_| \_\_|  |_|_____|_| \_\
"""
    console.print(Text(logo, style="bold green"))


def create_custom_progress_bar(
    current: int,
    total: int,
    width: int = 40,
    theme: str = "default",
    show_percentage: bool = True,
    show_numbers: bool = False,
    label: Optional[str] = None,
) -> str:
    """
    Create a custom progress bar with theme-aware styling.

    Args:
        current: Current progress value
        total: Total value
        width: Width of the progress bar
        theme: Theme name for styling
        show_percentage: Whether to show percentage
        show_numbers: Whether to show current/total numbers
        label: Optional label for the progress bar

    Returns:
        Formatted progress bar string
    """
    if total == 0:
        percentage = 0.0
    else:
        percentage = (current / total) * 100

    filled_width = int((current / total) * width) if total > 0 else 0
    empty_width = width - filled_width

    # Get theme elements
    theme_config = THEMES.get(theme, THEMES["default"])
    elements = VISUAL_ELEMENTS

    # Build progress bar
    bar = elements["progress_filled"] * filled_width + elements["progress_empty"] * empty_width

    # Build complete progress string
    parts = []
    if label:
        parts.append(label)

    parts.append(f"[{bar}]")

    if show_percentage:
        parts.append(f"{percentage:5.1f}%")

    if show_numbers:
        parts.append(f"({current}/{total})")

    return " ".join(parts)


def create_spinner(text: str = "Loading...") -> Live:
    """
    Create a spinner for long-running operations.

    Args:
        text: Loading text

    Returns:
        Live object with spinner

    Example:
        with create_spinner("Processing...") as spinner:
            # Do some work
            pass
    """
    spinner_text = Text(text, style="bold yellow")
    return Live(Align.center(spinner_text), console=console, refresh_per_second=10)
