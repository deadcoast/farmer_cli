"""
Theme showcase feature for Farmer CLI.

This module provides a visual demonstration of all available themes
and their various styling elements.
"""

from typing import Any
from typing import Dict

from rich.table import Table
from themes import THEMES
from themes import VISUAL_ELEMENTS

from ..ui.console import console
from ..ui.prompts import confirm_prompt
from ..ui.widgets import create_custom_progress_bar
from ..ui.widgets import create_frame
from .base import BaseFeature


class ThemeShowcaseFeature(BaseFeature):
    """
    Theme showcase feature implementation.

    Provides visual demonstrations of all available themes.
    """

    def __init__(self):
        """Initialize the theme showcase feature."""
        super().__init__(name="Theme Showcase", description="Visual demonstration of available themes")

    def execute(self) -> None:
        """Execute the theme showcase feature."""
        console.clear()
        console.print("[bold magenta]Theme Showcase[/bold magenta]\n")
        console.print("This showcase demonstrates all available themes and their visual elements.")

        if not confirm_prompt("\nWould you like to see all themes?"):
            return

        for theme_key, theme_data in THEMES.items():
            self._showcase_theme(theme_key, theme_data)

            if theme_key != list(THEMES.keys())[-1]:  # Not the last theme
                if not confirm_prompt("\nContinue to next theme?", default=True):
                    break

        console.print("\n[bold green]Theme showcase complete![/bold green]")
        console.input("Press Enter to return...")

    def _showcase_theme(self, theme_key: str, theme_data: Dict[str, Any]) -> None:
        """
        Showcase a single theme.

        Args:
            theme_key: Theme identifier
            theme_data: Theme configuration dictionary
        """
        console.clear()

        # Theme header
        name = theme_data.get("name", theme_key)
        description = theme_data.get("description", "")

        console.print(f"[{theme_data['title_style']}]Theme: {name}[/{theme_data['title_style']}]")
        if description:
            console.print(f"[{theme_data['subtitle_style']}]{description}[/{theme_data['subtitle_style']}]\n")

        # 1. Border styles demonstration
        console.print(f"[{theme_data['header_style']}]1. Border Styles[/{theme_data['header_style']}]")

        border_frame = create_frame(
            "This frame demonstrates\nthe border style and\ncharacter set used\nby this theme.",
            width=40,
            theme=theme_key,
            title="Sample Frame",
        )
        console.print(border_frame)
        console.print()

        # 2. Color palette
        console.print(f"[{theme_data['header_style']}]2. Color Palette[/{theme_data['header_style']}]")

        color_items = [
            ("Title", theme_data["title_style"], "Main headings"),
            ("Subtitle", theme_data["subtitle_style"], "Secondary headings"),
            ("Success", theme_data["success_style"], "Success messages"),
            ("Error", theme_data["error_style"], "Error messages"),
            ("Warning", theme_data["warning_style"], "Warning messages"),
            ("Info", theme_data["info_style"], "Information messages"),
            ("Prompt", theme_data["prompt_style"], "User prompts"),
        ]

        for label, style, desc in color_items:
            console.print(f"  {VISUAL_ELEMENTS['bullet']} [{style}]{label}[/{style}] - {desc}")
        console.print()

        # 3. Table styling
        console.print(f"[{theme_data['header_style']}]3. Table Styling[/{theme_data['header_style']}]")

        table = Table(
            title="Sample Data Table",
            style=theme_data.get("table_row_style", "white"),
            header_style=theme_data.get("table_header_style", "bold white on blue"),
        )

        table.add_column("ID", style="bold")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Progress")

        # Add sample rows with alternating colors
        for i in range(3):
            row_style = (
                theme_data["table_row_style"]
                if i % 2 == 0
                else theme_data.get("table_alt_row_style", theme_data["table_row_style"])
            )
            status = "Active" if i == 0 else "Pending" if i == 1 else "Complete"
            progress = create_custom_progress_bar(
                current=30 + i * 30, total=100, width=20, theme=theme_key, show_percentage=False
            )
            table.add_row(str(i + 1), f"Item {i + 1}", status, progress, style=row_style)

        console.print(table)
        console.print()

        # 4. Visual elements
        console.print(f"[{theme_data['header_style']}]4. Visual Elements[/{theme_data['header_style']}]")

        elements_display = []
        for elem_key, elem_char in list(VISUAL_ELEMENTS.items())[:10]:
            elements_display.append(f"{elem_char} {elem_key.replace('_', ' ').title()}")

        console.print("  " + "  ".join(elements_display[:5]))
        console.print("  " + "  ".join(elements_display[5:]))
        console.print()

        # 5. Progress indicators
        console.print(f"[{theme_data['header_style']}]5. Progress Indicators[/{theme_data['header_style']}]")

        for i, (label, value) in enumerate([("Download", 75), ("Processing", 45), ("Upload", 90)]):
            bar = create_custom_progress_bar(current=value, total=100, width=30, theme=theme_key, label=label.ljust(12))
            console.print(f"  {bar}")

        console.print()

        # 6. Code display
        console.print(f"[{theme_data['header_style']}]6. Code Display[/{theme_data['header_style']}]")

        code_sample = """def hello_world():
    print("Hello, World!")
    return True"""

        code_frame = create_frame(code_sample, width=40, theme=theme_key, padding=1)
        console.print(code_frame)

    def cleanup(self) -> None:
        """Cleanup the theme showcase feature."""
        # No specific cleanup needed for theme showcase
        pass
