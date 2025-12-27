"""
Entry point for the Farmer CLI application.

This module serves as the main entry point when running the package
as a module with `python -m farmer_cli`.

It routes to either CLI mode (with arguments) or interactive mode (without arguments).

Feature: farmer-cli-completion
Requirements: 13.6
"""

import atexit
import sys
from typing import Optional

from .ui.console import console
from .utils.cleanup import cleanup_handler


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the Farmer CLI application.

    Routes to CLI mode if arguments are provided, otherwise starts interactive mode.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Register cleanup handler
    atexit.register(cleanup_handler)

    # Get arguments
    argv = args if args is not None else sys.argv[1:]

    try:
        # Check if we have CLI arguments (excluding empty list)
        # If arguments are provided, use Click CLI
        # If no arguments, also use Click CLI which will start interactive mode
        from .cli import main as cli_main

        return cli_main()

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Application interrupted by user.[/bold yellow]")
        return 130  # Standard exit code for Ctrl+C
    except SystemExit as e:
        # Re-raise SystemExit to preserve exit codes from CLI
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
