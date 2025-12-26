"""
Layout management for Farmer CLI.

This module provides layout creation and management functions
for organizing the UI structure.
"""

from rich.layout import Layout
from rich.text import Text


def create_main_layout() -> Layout:
    """
    Create the main application layout.

    Returns:
        Configured Layout instance with header, body, and footer
    """
    layout = Layout()

    # Split into three sections
    layout.split_column(Layout(name="header", size=3), Layout(name="body", ratio=1), Layout(name="footer", size=1))

    # Configure header
    layout["header"].update(Text("=== Interactive CLI Menu ===", style="bold blue", justify="center"))

    # Footer will show contextual help
    layout["footer"].update(Text("Press Ctrl+C to exit.", style="dim", justify="center"))

    return layout


def create_split_layout(left_content, right_content, split_ratio: float = 0.5) -> Layout:
    """
    Create a horizontally split layout.

    Args:
        left_content: Content for the left panel
        right_content: Content for the right panel
        split_ratio: Ratio for splitting (0.5 = equal split)

    Returns:
        Configured Layout instance
    """
    layout = Layout()

    # Split horizontally
    layout.split_row(
        Layout(left_content, name="left", ratio=int(split_ratio)),
        Layout(right_content, name="right", ratio=int(1 - split_ratio)),
    )

    return layout


def create_dashboard_layout() -> Layout:
    """
    Create a dashboard-style layout with multiple panels.

    Returns:
        Configured Layout instance for dashboard view
    """
    layout = Layout()

    # Create main structure
    layout.split_column(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=3))

    # Split main area into panels
    layout["main"].split_row(Layout(name="sidebar", ratio=int(0.3)), Layout(name="content", ratio=int(0.7)))

    # Further split content area
    layout["content"].split_column(
        Layout(name="top_panel", ratio=int(0.5)), Layout(name="bottom_panel", ratio=int(0.5))
    )

    return layout


def update_layout_footer(layout: Layout, text: str, style: str = "dim") -> None:
    """
    Update the footer of a layout.

    Args:
        layout: Layout to update
        text: Footer text
        style: Text style
    """
    try:
        layout["footer"].update(Text(text, style=style, justify="center"))
    except KeyError:
        pass  # Footer not found in layout


def update_layout_header(layout: Layout, text: str, style: str = "bold blue") -> None:
    """
    Update the header of a layout.

    Args:
        layout: Layout to update
        text: Header text
        style: Text style
    """
    try:
        layout["header"].update(Text(text, style=style, justify="center"))
    except KeyError:
        pass  # Header not found in layout
