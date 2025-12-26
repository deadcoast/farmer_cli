"""
Data processing feature for Farmer CLI.

This module provides data processing functionality including
code snippets, system info, tables, and progress simulations.
"""

import platform
import sys
from time import sleep

from rich.align import Align
from rich.syntax import Syntax

from ..core.constants import DATA_PROCESSING_OPTIONS
from ..ui.console import console
from ..ui.menu import MenuManager
from ..ui.widgets import create_table
from ..ui.widgets import show_progress
from .base import BaseFeature


class DataProcessingFeature(BaseFeature):
    """
    Data processing feature implementation.

    Provides various data processing and display functionalities.
    """

    def __init__(self):
        """Initialize the data processing feature."""
        super().__init__(name="Data Processing", description="Advanced data processing and analysis tools")
        self.menu_manager = MenuManager()

    def execute(self) -> None:
        """Execute the data processing feature."""
        while True:
            choice = self.menu_manager.display_submenu("Data Processing Menu", DATA_PROCESSING_OPTIONS)

            if choice is None:
                break

            if choice == "1":
                self._display_code_snippet()
            elif choice == "2":
                self._show_system_info()
            elif choice == "3":
                self._display_sample_table()
            elif choice == "4":
                self._simulate_progress()

    def _display_code_snippet(self) -> None:
        """Display a syntax-highlighted code snippet."""
        console.clear()

        code = '''
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Example usage
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
'''

        syntax = Syntax(code.strip(), "python", theme="monokai", line_numbers=True, word_wrap=True)

        console.print("\n[bold cyan]Python Code Example:[/bold cyan]\n")
        console.print(syntax)
        console.input("\nPress Enter to return to the menu...")

    def _show_system_info(self) -> None:
        """Display system information."""
        console.clear()

        info = f"""
[bold green]System Information[/bold green]

System: {platform.system()}
Node Name: {platform.node()}
Release: {platform.release()}
Version: {platform.version()}
Machine: {platform.machine()}
Processor: {platform.processor() or "N/A"}
Python Version: {sys.version.split()[0]}
Python Implementation: {platform.python_implementation()}
        """

        console.print(Align.center(info.strip()))
        console.input("\nPress Enter to return to the menu...")

    def _display_sample_table(self) -> None:
        """Display a sample data table."""
        console.clear()

        # Create sample data
        columns = [
            ("ID", {"style": "dim", "width": 6}),
            ("Name", {"style": "bold cyan"}),
            ("Type", {"style": "magenta"}),
            ("Status", {"style": "green"}),
            ("Description", {"style": "dim"}),
        ]

        rows = [
            ["1", "Dataset A", "CSV", "Active", "Customer transaction data"],
            ["2", "Dataset B", "JSON", "Active", "Product inventory"],
            ["3", "Dataset C", "XML", "Archived", "Historical records"],
            ["4", "Dataset D", "Parquet", "Processing", "Analytics data"],
            ["5", "Dataset E", "CSV", "Error", "Corrupted file"],
        ]

        table = create_table("Sample Data Overview", columns, rows, show_lines=True)  # type: ignore

        console.print("\n")
        console.print(table)
        console.input("\nPress Enter to return to the menu...")

    def _simulate_progress(self) -> None:
        """Simulate a progress bar."""
        console.clear()
        console.print("\n[bold cyan]Processing Simulation[/bold cyan]\n")

        with show_progress("Processing data", total=100) as progress:
            task = progress.add_task("Analyzing...", total=100)

            for i in range(100):
                # Simulate work
                sleep(0.05)

                # Update progress
                progress.update(task, advance=1, description=f"Processing item {i + 1}/100")

        console.print("\n[bold green]✓ Processing complete![/bold green]")
        console.input("\nPress Enter to return to the menu...")

    def cleanup(self) -> None:
        """Cleanup the data processing feature."""
        # No specific cleanup needed for data processing
        pass
