"""
Entry point for the Farmer CLI application.

This module serves as the main entry point when running the package
as a module with `python -m farmer_cli`.
"""

import atexit
import sys
from typing import Optional

from .core.app import FarmerCLI
from .ui.console import console
from .utils.cleanup import cleanup_handler


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the Farmer CLI application.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Register cleanup handler
    atexit.register(cleanup_handler)

    try:
        # Create and run the application
        app = FarmerCLI()
        return app.run(args or sys.argv[1:])
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Application interrupted by user.[/bold yellow]")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
