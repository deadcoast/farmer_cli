"""
Click-based CLI interface for Farmer CLI.

This module provides the command-line interface using Click for argument parsing.
It supports both direct command execution and interactive mode.

Feature: farmer-cli-completion
Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .exceptions import DownloadError
from .exceptions import FormatError
from .exceptions import ValidationError
from .services.download_manager import DownloadManager
from .services.format_selector import FormatSelector
from .services.preferences import PreferencesService
from .services.ytdlp_wrapper import DownloadProgress
from .services.ytdlp_wrapper import YtdlpWrapper
from .ui.console import console
from .utils.url_utils import is_valid_url


logger = logging.getLogger(__name__)


class QuietContext:
    """Context object to track quiet mode across commands."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def echo(self, message: str, **kwargs) -> None:
        """Print message unless in quiet mode."""
        if not self.quiet:
            click.echo(message, **kwargs)

    def print(self, message: str, **kwargs) -> None:
        """Print rich message unless in quiet mode."""
        if not self.quiet:
            console.print(message, **kwargs)


pass_context = click.make_pass_decorator(QuietContext, ensure=True)


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    "-V",
    is_flag=True,
    help="Show version and exit.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output suitable for scripts.",
)
@click.pass_context
def cli(ctx: click.Context, version: bool, quiet: bool) -> None:
    """
    Farmer CLI - Video downloading and system management.

    Run without arguments to start interactive mode.
    Use --help with any command for more information.
    """
    # Store quiet context for subcommands
    ctx.ensure_object(QuietContext)
    ctx.obj = QuietContext(quiet=quiet)

    if version:
        click.echo(f"farmer-cli version {__version__}")
        ctx.exit(0)

    # If no subcommand is provided, run interactive mode
    if ctx.invoked_subcommand is None:
        # Import here to avoid circular imports
        from .core.app import FarmerCLI

        app = FarmerCLI()
        exit_code = app.run([])
        ctx.exit(exit_code)


@cli.command()
@click.argument("url")
@click.option(
    "--format",
    "-f",
    "format_id",
    default=None,
    help="Video format ID or quality preset (e.g., 'best', '1080p', '720p', 'audio').",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(),
    default=None,
    help="Output directory for downloaded files.",
)
@pass_context
def download(
    ctx: QuietContext,
    url: str,
    format_id: Optional[str],
    output_path: Optional[str],
) -> None:
    """
    Download a video from URL.

    URL is the video URL to download from supported platforms
    (YouTube, Vimeo, and many others).

    Examples:

        farmer-cli download "https://youtube.com/watch?v=..."

        farmer-cli download -f 720p -o ~/Videos "https://youtube.com/watch?v=..."

        farmer-cli download --quiet "https://youtube.com/watch?v=..."
    """
    # Validate URL
    if not is_valid_url(url):
        ctx.print("[bold red]Error:[/bold red] Invalid or unsupported URL")
        raise SystemExit(1)

    try:
        # Initialize services
        preferences_service = PreferencesService()
        ytdlp_wrapper = YtdlpWrapper()
        format_selector = FormatSelector(
            ytdlp_wrapper=ytdlp_wrapper,
            preferences_service=preferences_service,
        )

        # Determine output path
        if output_path:
            out_dir = Path(output_path).expanduser()
        else:
            default_path = preferences_service.get("download_directory")
            if default_path:
                out_dir = Path(default_path)
            else:
                out_dir = Path.home() / "Downloads" / "FarmerCLI"

        # Create output directory if needed
        out_dir.mkdir(parents=True, exist_ok=True)

        ctx.print("[dim]Fetching video information...[/dim]")

        # Extract video info
        video_info = ytdlp_wrapper.extract_info(url)

        ctx.print(f"[bold]Title:[/bold] {video_info.title}")
        if video_info.uploader:
            ctx.print(f"[bold]Channel:[/bold] {video_info.uploader}")

        # Determine format
        selected_format = None
        if format_id:
            # Check if it's a preset
            if format_id.lower() in ("best", "1080p", "720p", "480p", "360p", "audio"):
                if format_id.lower() == "best":
                    selected_format = format_selector.get_best_format(video_info.formats)
                elif format_id.lower() == "audio":
                    audio_formats = format_selector.get_audio_formats(video_info.formats)
                    if audio_formats:
                        selected_format = audio_formats[0]
                else:
                    # Find format matching resolution
                    for fmt in video_info.formats:
                        if fmt.resolution and format_id.lower() in fmt.resolution.lower():
                            selected_format = fmt
                            break
            else:
                # Treat as format ID
                for fmt in video_info.formats:
                    if fmt.format_id == format_id:
                        selected_format = fmt
                        break

        if not selected_format:
            selected_format = format_selector.get_best_format(video_info.formats)

        if selected_format:
            ctx.print(
                f"[bold]Format:[/bold] {selected_format.resolution or 'audio'} "
                f"({selected_format.extension})"
            )

        ctx.print(f"[bold]Output:[/bold] {out_dir}")
        ctx.print("[bold green]Starting download...[/bold green]")

        # Download with progress
        def progress_callback(progress: DownloadProgress) -> None:
            if not ctx.quiet:
                percent = progress.percent
                speed = progress.speed_formatted
                console.print(
                    f"\r[cyan]Progress:[/cyan] {percent:.1f}% - {speed}",
                    end="",
                )

        file_path = ytdlp_wrapper.download(
            url=url,
            output_path=out_dir,
            format_id=selected_format.format_id if selected_format else None,
            progress_callback=progress_callback,
        )

        if not ctx.quiet:
            console.print()  # New line after progress

        ctx.print("\n[bold green]✓ Download complete![/bold green]")
        ctx.print(f"[bold]Saved to:[/bold] {file_path}")

        # Record in history
        from .core.database import get_session

        download_manager = DownloadManager(
            session_factory=get_session,
            default_output_path=out_dir,
        )
        path = Path(file_path)
        download_manager.add_to_history(
            url=url,
            title=video_info.title,
            file_path=file_path,
            file_size=path.stat().st_size if path.exists() else None,
            duration=video_info.duration,
            uploader=video_info.uploader,
        )

    except DownloadError as e:
        ctx.print(f"[bold red]Download error:[/bold red] {e.message}")
        logger.error(f"Download error: {e}")
        raise SystemExit(1) from e
    except FormatError as e:
        ctx.print(f"[bold red]Format error:[/bold red] {e.message}")
        logger.error(f"Format error: {e}")
        raise SystemExit(1) from e
    except ValidationError as e:
        ctx.print(f"[bold red]Validation error:[/bold red] {e.message}")
        logger.error(f"Validation error: {e}")
        raise SystemExit(1) from e
    except Exception as e:
        ctx.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise SystemExit(1) from e


@cli.command()
@pass_context
def interactive(ctx: QuietContext) -> None:
    """
    Start interactive mode with Rich UI.

    This is the default mode when running farmer-cli without arguments.
    """
    from .core.app import FarmerCLI

    app = FarmerCLI()
    exit_code = app.run([])
    raise SystemExit(exit_code)


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        cli(standalone_mode=False)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:
        click.echo("Aborted!", err=True)
        return 1
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user.", err=True)
        return 130
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.error(f"CLI error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
