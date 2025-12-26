"""
File browser feature for Farmer CLI.

This module provides file and directory browsing functionality
with detailed information display.
"""

import logging
from pathlib import Path
from typing import List

from ..ui.console import console
from ..ui.prompts import text_prompt
from ..ui.widgets import create_table


logger = logging.getLogger(__name__)


def browse_files() -> None:
    """Browse files and directories."""
    console.clear()
    console.print("[bold cyan]File Browser[/bold cyan]\n")

    directory = text_prompt(
        "Enter directory path",
        default=".",
        validator=lambda x: Path(x).exists(),
        error_message="Directory does not exist",
    )

    try:
        list_directory(Path(directory))
    except Exception as e:
        console.print(f"[bold red]Error browsing directory: {e}[/bold red]")
        logger.error(f"File browser error: {e}")

    console.input("\nPress Enter to return...")


def list_directory(directory: Path) -> None:
    """
    List contents of a directory.

    Args:
        directory: Directory path to list
    """
    if not directory.is_dir():
        console.print(f"[bold red]{directory} is not a directory[/bold red]")
        return

    try:
        # Get directory contents
        items = list(directory.iterdir())

        if not items:
            console.print(f"[bold yellow]Directory {directory} is empty[/bold yellow]")
            return

        # Prepare data for table
        columns = [
            ("Name", {"style": "bold cyan", "no_wrap": True}),
            ("Type", {"style": "magenta", "width": 8}),
            ("Size", {"style": "green", "width": 12}),
            ("Modified", {"style": "dim", "width": 19}),
            ("Permissions", {"style": "dim", "width": 10}),
        ]

        rows = [get_file_info(item) for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower()))]
        # Create and display table
        table = create_table(f"Contents of {directory.resolve()}", columns, rows, show_lines=True)

        console.print(table)

        # Show summary
        dirs = sum(bool(item.is_dir()) for item in items)
        files = len(items) - dirs
        console.print(f"\n[dim]{dirs} directories, {files} files[/dim]")

    except PermissionError:
        console.print(f"[bold red]Permission denied: {directory}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error reading directory: {e}[/bold red]")
        logger.error(f"Error listing directory {directory}: {e}")


def get_file_info(path: Path) -> List[str]:
    """
    Get file information for display.

    Args:
        path: File or directory path

    Returns:
        List of file information strings
    """
    try:
        stat = path.stat()

        # Name (with / for directories)
        name = path.name
        if path.is_dir():
            name += "/"

        # Type
        if path.is_dir():
            file_type = "Dir"
        elif path.is_symlink():
            file_type = "Link"
        else:
            file_type = path.suffix[1:].upper() or "File"

        # Size
        size = format_size(stat.st_size) if path.is_file() else "-"
        # Modified time
        from datetime import datetime

        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        # Permissions (Unix-style)
        perms = format_permissions(stat.st_mode)

        return [name, file_type, size, modified, perms]

    except Exception as e:
        logger.warning(f"Error getting info for {path}: {e}")
        return [path.name, "?", "?", "?", "?"]


def format_size(size: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:,.1f} {unit}"
        size //= 1024
    return f"{size:,.1f} PB"


def format_permissions(mode: int) -> str:
    """
    Format file permissions in Unix style.

    Args:
        mode: File mode from stat

    Returns:
        Permission string (e.g., "rwxr-xr-x")
    """
    import stat

    perms = [
        "r" if mode & stat.S_IRUSR else "-",
        "w" if mode & stat.S_IWUSR else "-",
        "x" if mode & stat.S_IXUSR else "-",
        "r" if mode & stat.S_IRGRP else "-",
        "w" if mode & stat.S_IWGRP else "-",
    ]

    perms.append("x" if mode & stat.S_IXGRP else "-")

    # Other permissions
    perms.append("r" if mode & stat.S_IROTH else "-")
    perms.append("w" if mode & stat.S_IWOTH else "-")
    perms.append("x" if mode & stat.S_IXOTH else "-")

    return "".join(perms)
