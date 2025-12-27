"""
Export functionality for Farmer CLI.

This module provides export capabilities for various data formats
including CSV, JSON, and PDF.
"""

import csv
import logging
from pathlib import Path
from typing import Any
from typing import Optional

from ..core.constants import CSV_EXPORT_FILE
from ..core.constants import HTML_TEMP_FILE
from ..core.constants import PDF_EXPORT_FILE
from ..core.database import get_session
from ..models.user import User
from ..services.export import ExportFormat
from ..services.export import ExportResult
from ..services.export import ExportService
from ..ui.console import console
from .base import BaseFeature


logger = logging.getLogger(__name__)

# Check if pdfkit is available
try:
    import pdfkit

    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

# Check if reportlab is available (alternative PDF generation)
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Spacer

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ExportFeature(BaseFeature):
    """
    Export feature implementation.

    Provides data export functionality in various formats.
    """

    def __init__(self):
        """Initialize the export feature."""
        super().__init__(name="Export", description="Export data to various formats")
        self._export_service = ExportService()

    def execute(self, export_type: str = "csv", **kwargs: Any) -> None:
        """
        Execute export based on type.

        Args:
            export_type: Type of export (csv, json, pdf)
            **kwargs: Additional arguments for specific export types
        """
        if export_type == "csv":
            self.export_users_csv()
        elif export_type == "json":
            self.export_users_json()
        elif export_type == "pdf":
            export_help_to_pdf()
        elif export_type == "history_csv":
            self.export_history_csv()
        elif export_type == "history_json":
            self.export_history_json()
        elif export_type == "history_pdf":
            self.export_history_pdf()
        else:
            console.print(f"[bold red]Unknown export type: {export_type}[/bold red]")

    def export_users_csv(self, filename: Optional[str] = None) -> ExportResult | None:
        """
        Export users to CSV file using the export service.

        Args:
            filename: Output filename (defaults to CSV_EXPORT_FILE)

        Returns:
            ExportResult or None if export fails
        """
        output_file = Path(filename or CSV_EXPORT_FILE)

        try:
            result = self._export_service.export_users(
                output_path=output_file,
                format=ExportFormat.CSV,
            )
            self._report_export_result(result)
            return result
        except Exception as e:
            console.print(f"[bold red]Failed to export users to CSV: {e}[/bold red]")
            logger.error(f"Failed to export users to CSV: {e}")
            return None

    def export_users_json(self, filename: Optional[str] = None) -> ExportResult | None:
        """
        Export users to JSON file using the export service.

        Args:
            filename: Output filename (defaults to users_export.json)

        Returns:
            ExportResult or None if export fails
        """
        output_file = Path(filename or "users_export.json")

        try:
            result = self._export_service.export_users(
                output_path=output_file,
                format=ExportFormat.JSON,
            )
            self._report_export_result(result)
            return result
        except Exception as e:
            console.print(f"[bold red]Failed to export users to JSON: {e}[/bold red]")
            logger.error(f"Failed to export users to JSON: {e}")
            return None

    def export_history_csv(self, filename: Optional[str] = None) -> ExportResult | None:
        """
        Export download history to CSV file.

        Args:
            filename: Output filename (defaults to history_export.csv)

        Returns:
            ExportResult or None if export fails
        """
        output_file = Path(filename or "history_export.csv")

        try:
            result = self._export_service.export_history(
                output_path=output_file,
                format=ExportFormat.CSV,
            )
            self._report_export_result(result)
            return result
        except Exception as e:
            console.print(f"[bold red]Failed to export history to CSV: {e}[/bold red]")
            logger.error(f"Failed to export history to CSV: {e}")
            return None

    def export_history_json(self, filename: Optional[str] = None) -> ExportResult | None:
        """
        Export download history to JSON file.

        Args:
            filename: Output filename (defaults to history_export.json)

        Returns:
            ExportResult or None if export fails
        """
        output_file = Path(filename or "history_export.json")

        try:
            result = self._export_service.export_history(
                output_path=output_file,
                format=ExportFormat.JSON,
            )
            self._report_export_result(result)
            return result
        except Exception as e:
            console.print(f"[bold red]Failed to export history to JSON: {e}[/bold red]")
            logger.error(f"Failed to export history to JSON: {e}")
            return None

    def export_history_pdf(self, filename: Optional[str] = None) -> ExportResult | None:
        """
        Export download history to PDF file.

        Args:
            filename: Output filename (defaults to history_export.pdf)

        Returns:
            ExportResult or None if export fails
        """
        output_file = Path(filename or "history_export.pdf")

        try:
            result = self._export_service.export_history(
                output_path=output_file,
                format=ExportFormat.PDF,
            )
            self._report_export_result(result)
            return result
        except Exception as e:
            console.print(f"[bold red]Failed to export history to PDF: {e}[/bold red]")
            logger.error(f"Failed to export history to PDF: {e}")
            return None

    def _report_export_result(self, result: ExportResult) -> None:
        """
        Report export completion with file location and size.

        Args:
            result: The export result to report
        """
        if result.success:
            if result.record_count > 0:
                console.print(
                    f"[bold green]✓ {result.message}[/bold green]"
                )
                console.print(
                    f"[dim]  File: {result.file_path}[/dim]"
                )
                console.print(
                    f"[dim]  Size: {result.file_size_formatted}[/dim]"
                )
                console.print(
                    f"[dim]  Records: {result.record_count}[/dim]"
                )
            else:
                console.print(f"[bold yellow]{result.message}[/bold yellow]")
        else:
            console.print(f"[bold red]Export failed: {result.message}[/bold red]")

    def cleanup(self) -> None:
        """
        Cleanup the export feature.

        No cleanup required for this feature.
        """
        pass


def export_users_to_csv(filename: Optional[str] = None) -> None:
    """
    Export users to CSV file.

    Args:
        filename: Output filename (defaults to CSV_EXPORT_FILE)
    """
    output_file = Path(filename or CSV_EXPORT_FILE)

    try:
        with get_session() as session:
            users = session.query(User).order_by(User.name).all()

            if not users:
                console.print("[bold yellow]No users to export.[/bold yellow]")
                return

            # Write CSV file
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(["ID", "Name", "Preferences", "Created At", "Updated At"])

                # Write user data
                for user in users:
                    writer.writerow(
                        [user.id, user.name, user.preferences, user.created_at.isoformat(), user.updated_at.isoformat()]
                    )

            console.print(f"[bold green]✓ Exported {len(users)} users to {output_file}[/bold green]")
            logger.info(f"Exported {len(users)} users to {output_file}")

    except Exception as e:
        error_msg = f"Failed to export users to CSV: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise


def export_help_to_pdf(filename: Optional[str] = None) -> None:
    """
    Export help documentation to PDF.

    Args:
        filename: Output filename (defaults to PDF_EXPORT_FILE)
    """
    output_file = Path(filename or PDF_EXPORT_FILE)

    # Try reportlab first (pure Python solution)
    if REPORTLAB_AVAILABLE:
        try:
            console.print("[dim]Generating PDF using reportlab...[/dim]")
            generate_help_pdf_with_reportlab(str(output_file))
            console.print(f"[bold green]✓ Help documentation exported to {output_file}[/bold green]")
            logger.info(f"Exported help documentation to {output_file} using reportlab")
            return
        except Exception as e:
            logger.warning(f"Reportlab PDF generation failed: {e}")
            console.print("[bold yellow]Reportlab failed, trying alternative methods...[/bold yellow]")

    # Try pdfkit if reportlab is not available or failed
    temp_html = Path(HTML_TEMP_FILE)
    can_use_pdfkit = False

    if PDFKIT_AVAILABLE:
        try:
            # Test if wkhtmltopdf is available
            import subprocess

            result = subprocess.run(["which", "wkhtmltopdf"], capture_output=True, text=True)
            if result.returncode == 0:
                can_use_pdfkit = True
        except Exception:
            pass

    if can_use_pdfkit:
        try:
            # Generate HTML content
            html_content = generate_help_html()

            # Write temporary HTML file
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Convert to PDF using pdfkit
            console.print("[dim]Generating PDF using pdfkit...[/dim]")
            pdfkit.from_file(str(temp_html), str(output_file))

            console.print(f"[bold green]✓ Help documentation exported to {output_file}[/bold green]")
            logger.info(f"Exported help documentation to {output_file} using pdfkit")
            return

        except Exception as e:
            error_msg = f"PDFKit export failed: {e}"
            console.print(f"[bold yellow]{error_msg}[/bold yellow]")
            logger.warning(error_msg)
        finally:
            # Clean up temporary file
            if temp_html.exists():
                temp_html.unlink()

    # Final fallback to HTML export
    html_file = output_file.with_suffix(".html")
    console.print(
        f"[bold yellow]Note: PDF generation unavailable. " f"Exporting to HTML instead: {html_file}[/bold yellow]"
    )

    try:
        # Generate and save HTML content
        html_content = generate_help_html()
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        console.print(f"[bold green]✓ Help documentation exported to {html_file}[/bold green]")
        console.print("[dim]You can open this file in your browser and print to PDF if needed.[/dim]")
        logger.info(f"Exported help documentation to HTML: {html_file}")

    except Exception as e:
        error_msg = f"Failed to export help: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise


def generate_help_pdf_with_reportlab(filename: str) -> None:
    """
    Generate PDF using reportlab (pure Python solution).

    Args:
        filename: Output PDF filename
    """
    from ..core.constants import APP_NAME
    from ..core.constants import APP_VERSION

    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.HexColor("#34495e"),
        spaceAfter=12,
        spaceBefore=20,
    )

    feature_style = ParagraphStyle("Feature", parent=styles["Normal"], fontSize=12, leftIndent=20, spaceAfter=10)

    # Add content
    story.append(Paragraph(f"{APP_NAME} v{APP_VERSION}", title_style))
    story.append(Paragraph("Help Documentation", styles["Heading2"]))
    story.append(Spacer(1, 0.5 * inch))

    # Overview
    story.append(Paragraph("Overview", heading_style))
    story.append(
        Paragraph(
            f"{APP_NAME} is a powerful command-line interface application with a rich terminal UI "
            "for managing various tasks including data processing, user management, and system tools.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Features
    features = [
        (
            "Data Processing",
            [
                "Code snippet display with syntax highlighting",
                "System information viewer",
                "Data table visualization",
                "Progress simulation and monitoring",
            ],
        ),
        (
            "User Management",
            [
                "Add new users with custom preferences",
                "List all users with detailed information",
                "Export user data to CSV format",
                "JSON-based preference storage",
            ],
        ),
        (
            "Configuration",
            [
                "Multiple theme options (default, dark, light, high contrast)",
                "Date and time display",
                "Searchable help system",
                "Preference persistence",
            ],
        ),
        (
            "System Tools",
            [
                "File browser with detailed file information",
                "Weather checking for any city",
                "PDF export for documentation",
                "Feedback submission system",
            ],
        ),
    ]

    story.append(Paragraph("Main Features", heading_style))

    for feature_name, items in features:
        story.append(Paragraph(f"<b>{feature_name}</b>", feature_style))
        for item in items:
            story.extend([Paragraph(f"• {item}", feature_style), Spacer(1, 0.2 * inch)])
        story.append(Spacer(1, 0.2 * inch))

    # Keyboard shortcuts
    story.append(Paragraph("Keyboard Shortcuts", heading_style))
    shortcuts = [
        ("Ctrl+C", "Exit the application"),
        ("Ctrl+S", "Search menu options"),
        ("Ctrl+H", "Display help"),
        ("0", "Return to previous menu"),
    ]

    for key, desc in shortcuts:
        story.append(Paragraph(f"<b>{key}</b> - {desc}", feature_style))

    story.append(Spacer(1, 0.3 * inch))

    # Usage tips
    story.append(Paragraph("Usage Tips", heading_style))
    tips = [
        "Type 'help' at any menu to get context-sensitive help",
        "Use number keys to quickly select menu options",
        "Press '0' to return to the previous menu",
        "All data is automatically saved to the local database",
        "Preferences are persisted between sessions",
    ]

    for tip in tips:
        story.extend([Paragraph(f"• {tip}", feature_style), Spacer(1, 0.2 * inch)])

    # Build PDF
    doc.build(story)


def generate_help_html() -> str:
    """
    Generate HTML content for help documentation.

    Returns:
        HTML string
    """
    from ..core.constants import APP_NAME
    from ..core.constants import APP_VERSION

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{APP_NAME} - Help Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .feature {{
            background: #ecf0f1;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #3498db;
            border-radius: 5px;
        }}
        .shortcut {{
            background: #e8f5e9;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        }}
        code {{
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{APP_NAME} v{APP_VERSION} - Help Documentation</h1>

        <h2>Overview</h2>
        <p>{APP_NAME} is a powerful command-line interface application with a rich terminal UI
        for managing various tasks including data processing, user management, and system tools.</p>

        <h2>Main Features</h2>

        <div class="feature">
            <h3>1. Data Processing</h3>
            <p>Advanced data processing and analysis tools including:</p>
            <ul>
                <li>Code snippet display with syntax highlighting</li>
                <li>System information viewer</li>
                <li>Data table visualization</li>
                <li>Progress simulation and monitoring</li>
            </ul>
        </div>

        <div class="feature">
            <h3>2. User Management</h3>
            <p>Complete user management system with:</p>
            <ul>
                <li>Add new users with custom preferences</li>
                <li>List all users with detailed information</li>
                <li>Export user data to CSV format</li>
                <li>JSON-based preference storage</li>
            </ul>
        </div>

        <div class="feature">
            <h3>3. Configuration</h3>
            <p>Customize your experience with:</p>
            <ul>
                <li>Multiple theme options (default, dark, light, high contrast)</li>
                <li>Date and time display</li>
                <li>Searchable help system</li>
                <li>Preference persistence</li>
            </ul>
        </div>

        <div class="feature">
            <h3>4. System Tools</h3>
            <p>Useful system utilities including:</p>
            <ul>
                <li>File browser with detailed file information</li>
                <li>Weather checking for any city</li>
                <li>PDF export for documentation</li>
                <li>Feedback submission system</li>
            </ul>
        </div>

        <h2>Keyboard Shortcuts</h2>
        <div class="shortcut">Ctrl+C - Exit the application</div>
        <div class="shortcut">Ctrl+S - Search menu options</div>
        <div class="shortcut">Ctrl+H - Display help</div>

        <h2>Usage Tips</h2>
        <ul>
            <li>Type <code>help</code> at any menu to get context-sensitive help</li>
            <li>Use number keys to quickly select menu options</li>
            <li>Press <code>0</code> to return to the previous menu</li>
            <li>All data is automatically saved to the local database</li>
            <li>Preferences are persisted between sessions</li>
        </ul>

        <h2>Configuration</h2>
        <p>The application can be configured through:</p>
        <ul>
            <li>Environment variables in <code>.env</code> file</li>
            <li>User preferences stored in <code>preferences.json</code></li>
            <li>Theme selection from the Configuration menu</li>
        </ul>

        <div class="footer">
            <p>For support, contact: support@farmercli.com</p>
            <p>Generated on: {Path.cwd().stat().st_ctime}</p>
        </div>
    </div>
</body>
</html>
"""
