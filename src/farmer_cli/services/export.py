"""
Enhanced export service for Farmer CLI.

This module provides comprehensive export and import functionality
for various data formats including CSV, JSON, and PDF.

Feature: farmer-cli-completion
Requirements: 12.1, 12.2, 12.3, 12.4, 12.6
"""

import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.database import get_session
from ..exceptions import ExportError
from ..exceptions import ValidationError
from ..models.history import DownloadHistory
from ..models.user import User


logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


@dataclass
class ExportResult:
    """
    Result of an export operation.

    Attributes
    ----------
    success : bool
        Whether the export was successful
    file_path : Path
        Path to the exported file
    file_size : int
        Size of the exported file in bytes
    record_count : int
        Number of records exported
    format : ExportFormat
        Format of the export
    message : str
        Human-readable result message
    """

    success: bool
    file_path: Path
    file_size: int
    record_count: int
    format: ExportFormat
    message: str

    @property
    def file_size_formatted(self) -> str:
        """
        Get human-readable file size.

        Returns
        -------
        str
            Formatted file size (e.g., "1.5 KB")
        """
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class ImportResult:
    """
    Result of an import operation.

    Attributes
    ----------
    success : bool
        Whether the import was successful
    records_imported : int
        Number of records successfully imported
    records_skipped : int
        Number of records skipped (duplicates, invalid)
    errors : list[str]
        List of error messages for failed records
    message : str
        Human-readable result message
    """

    success: bool
    records_imported: int
    records_skipped: int
    errors: list[str]
    message: str


class ExportService:
    """
    Enhanced export service with multiple formats.

    Provides export functionality for users and download history
    in CSV, JSON, and PDF formats, as well as import functionality
    for JSON format.
    """

    # Default fields for user export
    USER_FIELDS = ["id", "name", "preferences", "created_at", "updated_at"]

    # Default fields for history export
    HISTORY_FIELDS = [
        "id",
        "url",
        "title",
        "file_path",
        "file_size",
        "format_id",
        "duration",
        "uploader",
        "downloaded_at",
        "status",
    ]

    def __init__(self) -> None:
        """Initialize the export service."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def export_users(
        self,
        output_path: Path,
        format: ExportFormat = ExportFormat.JSON,
        fields: list[str] | None = None,
    ) -> ExportResult:
        """
        Export users to specified format.

        Parameters
        ----------
        output_path : Path
            Path for the output file
        format : ExportFormat
            Export format (CSV, JSON, or PDF)
        fields : list[str] | None
            Fields to include (None for all fields)

        Returns
        -------
        ExportResult
            Result of the export operation

        Raises
        ------
        ExportError
            If export fails
        """
        fields = fields or self.USER_FIELDS
        self._validate_fields(fields, self.USER_FIELDS, "user")

        try:
            with get_session() as session:
                users = session.query(User).order_by(User.name).all()

                if not users:
                    return ExportResult(
                        success=True,
                        file_path=output_path,
                        file_size=0,
                        record_count=0,
                        format=format,
                        message="No users to export",
                    )

                # Convert users to dictionaries
                data = [self._user_to_dict(user, fields) for user in users]

                # Export based on format
                if format == ExportFormat.JSON:
                    self._export_to_json(data, output_path)
                elif format == ExportFormat.CSV:
                    self._export_to_csv(data, output_path, fields)
                elif format == ExportFormat.PDF:
                    self._export_users_to_pdf(data, output_path, fields)

                file_size = output_path.stat().st_size
                self._logger.info(
                    f"Exported {len(users)} users to {output_path} ({format.value})"
                )

                return ExportResult(
                    success=True,
                    file_path=output_path,
                    file_size=file_size,
                    record_count=len(users),
                    format=format,
                    message=f"Successfully exported {len(users)} users to {output_path}",
                )

        except Exception as e:
            self._logger.error(f"Failed to export users: {e}")
            raise ExportError(f"Failed to export users: {e}") from e

    def export_history(
        self,
        output_path: Path,
        format: ExportFormat = ExportFormat.JSON,
        fields: list[str] | None = None,
    ) -> ExportResult:
        """
        Export download history to specified format.

        Parameters
        ----------
        output_path : Path
            Path for the output file
        format : ExportFormat
            Export format (CSV, JSON, or PDF)
        fields : list[str] | None
            Fields to include (None for all fields)

        Returns
        -------
        ExportResult
            Result of the export operation

        Raises
        ------
        ExportError
            If export fails
        """
        fields = fields or self.HISTORY_FIELDS
        self._validate_fields(fields, self.HISTORY_FIELDS, "history")

        try:
            with get_session() as session:
                history = (
                    session.query(DownloadHistory)
                    .order_by(DownloadHistory.downloaded_at.desc())
                    .all()
                )

                if not history:
                    return ExportResult(
                        success=True,
                        file_path=output_path,
                        file_size=0,
                        record_count=0,
                        format=format,
                        message="No download history to export",
                    )

                # Convert history entries to dictionaries
                data = [self._history_to_dict(entry, fields) for entry in history]

                # Export based on format
                if format == ExportFormat.JSON:
                    self._export_to_json(data, output_path)
                elif format == ExportFormat.CSV:
                    self._export_to_csv(data, output_path, fields)
                elif format == ExportFormat.PDF:
                    self._export_history_to_pdf(data, output_path, fields)

                file_size = output_path.stat().st_size
                self._logger.info(
                    f"Exported {len(history)} history entries to {output_path} ({format.value})"
                )

                return ExportResult(
                    success=True,
                    file_path=output_path,
                    file_size=file_size,
                    record_count=len(history),
                    format=format,
                    message=f"Successfully exported {len(history)} history entries to {output_path}",
                )

        except Exception as e:
            self._logger.error(f"Failed to export history: {e}")
            raise ExportError(f"Failed to export history: {e}") from e

    def import_data(
        self,
        file_path: Path,
        data_type: str = "users",
    ) -> ImportResult:
        """
        Import data from JSON file.

        Parameters
        ----------
        file_path : Path
            Path to the JSON file to import
        data_type : str
            Type of data to import ("users" or "history")

        Returns
        -------
        ImportResult
            Result of the import operation

        Raises
        ------
        ExportError
            If import fails
        ValidationError
            If data validation fails
        """
        if not file_path.exists():
            raise ExportError(f"Import file not found: {file_path}")

        if not file_path.suffix.lower() == ".json":
            raise ExportError("Only JSON format is supported for import")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValidationError("Import data must be a JSON array")

            if data_type == "users":
                return self._import_users(data)
            elif data_type == "history":
                return self._import_history(data)
            else:
                raise ValidationError(f"Unknown data type: {data_type}")

        except json.JSONDecodeError as e:
            raise ExportError(f"Invalid JSON file: {e}") from e
        except Exception as e:
            if isinstance(e, (ExportError, ValidationError)):
                raise
            self._logger.error(f"Failed to import data: {e}")
            raise ExportError(f"Failed to import data: {e}") from e

    def _export_to_json(self, data: list[dict], output_path: Path) -> None:
        """
        Export data to JSON format.

        Parameters
        ----------
        data : list[dict]
            Data to export
        output_path : Path
            Output file path
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    def _export_to_csv(
        self, data: list[dict], output_path: Path, fields: list[str]
    ) -> None:
        """
        Export data to CSV format.

        Parameters
        ----------
        data : list[dict]
            Data to export
        output_path : Path
            Output file path
        fields : list[str]
            Fields to include as columns
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

    def _export_users_to_pdf(
        self, data: list[dict], output_path: Path, fields: list[str]
    ) -> None:
        """
        Export users to PDF format.

        Parameters
        ----------
        data : list[dict]
            User data to export
        output_path : Path
            Output file path
        fields : list[str]
            Fields to include
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph("User Export", styles["Heading1"]))
            story.append(Spacer(1, 0.25 * inch))
            story.append(
                Paragraph(
                    f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 0.5 * inch))

            if data:
                # Create table data
                table_data = [fields]  # Header row
                for record in data:
                    row = [str(record.get(field, ""))[:50] for field in fields]
                    table_data.append(row)

                # Create table
                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(table)
            else:
                story.append(Paragraph("No users to export.", styles["Normal"]))

            doc.build(story)

        except ImportError:
            # Fallback to HTML if reportlab is not available
            self._export_to_html_fallback(data, output_path, fields, "User Export")

    def _export_history_to_pdf(
        self, data: list[dict], output_path: Path, fields: list[str]
    ) -> None:
        """
        Export download history to PDF format.

        Parameters
        ----------
        data : list[dict]
            History data to export
        output_path : Path
            Output file path
        fields : list[str]
            Fields to include
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(str(output_path), pagesize=landscape(letter))
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph("Download History Export", styles["Heading1"]))
            story.append(Spacer(1, 0.25 * inch))
            story.append(
                Paragraph(
                    f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 0.5 * inch))

            if data:
                # Create table data with truncated values
                table_data = [fields]  # Header row
                for record in data:
                    row = [str(record.get(field, ""))[:40] for field in fields]
                    table_data.append(row)

                # Create table
                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 7),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                        ]
                    )
                )
                story.append(table)
            else:
                story.append(Paragraph("No download history to export.", styles["Normal"]))

            doc.build(story)

        except ImportError:
            # Fallback to HTML if reportlab is not available
            self._export_to_html_fallback(data, output_path, fields, "Download History Export")

    def _export_to_html_fallback(
        self, data: list[dict], output_path: Path, fields: list[str], title: str
    ) -> None:
        """
        Export to HTML as fallback when PDF libraries are unavailable.

        Parameters
        ----------
        data : list[dict]
            Data to export
        output_path : Path
            Output file path (will be changed to .html)
        fields : list[str]
            Fields to include
        title : str
            Document title
        """
        html_path = output_path.with_suffix(".html")

        # Ensure parent directory exists
        html_path.parent.mkdir(parents=True, exist_ok=True)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <table>
        <tr>{''.join(f'<th>{field}</th>' for field in fields)}</tr>
"""
        for record in data:
            row = "".join(f"<td>{str(record.get(field, ''))[:100]}</td>" for field in fields)
            html_content += f"        <tr>{row}</tr>\n"

        html_content += """    </table>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self._logger.warning(
            f"PDF export unavailable, exported to HTML: {html_path}"
        )

    def _import_users(self, data: list[dict]) -> ImportResult:
        """
        Import users from JSON data.

        Parameters
        ----------
        data : list[dict]
            User data to import

        Returns
        -------
        ImportResult
            Result of the import operation
        """
        imported = 0
        skipped = 0
        errors = []

        with get_session() as session:
            for i, record in enumerate(data):
                try:
                    # Validate required fields
                    if "name" not in record:
                        errors.append(f"Record {i}: Missing required field 'name'")
                        skipped += 1
                        continue

                    name = str(record["name"]).strip()
                    if not name:
                        errors.append(f"Record {i}: Empty name")
                        skipped += 1
                        continue

                    # Check for duplicate
                    existing = session.query(User).filter(User.name == name).first()
                    if existing:
                        errors.append(f"Record {i}: User '{name}' already exists")
                        skipped += 1
                        continue

                    # Create user
                    preferences = record.get("preferences", "{}")
                    if isinstance(preferences, dict):
                        preferences = json.dumps(preferences)

                    user = User(name=name, preferences=preferences)
                    session.add(user)
                    imported += 1

                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
                    skipped += 1

            session.commit()

        self._logger.info(f"Imported {imported} users, skipped {skipped}")

        return ImportResult(
            success=imported > 0 or (imported == 0 and skipped == 0),
            records_imported=imported,
            records_skipped=skipped,
            errors=errors,
            message=f"Imported {imported} users, skipped {skipped}",
        )

    def _import_history(self, data: list[dict]) -> ImportResult:
        """
        Import download history from JSON data.

        Parameters
        ----------
        data : list[dict]
            History data to import

        Returns
        -------
        ImportResult
            Result of the import operation
        """
        imported = 0
        skipped = 0
        errors = []

        with get_session() as session:
            for i, record in enumerate(data):
                try:
                    # Validate required fields
                    required_fields = ["url", "title", "file_path"]
                    missing = [f for f in required_fields if f not in record]
                    if missing:
                        errors.append(f"Record {i}: Missing required fields: {missing}")
                        skipped += 1
                        continue

                    url = str(record["url"]).strip()
                    title = str(record["title"]).strip()
                    file_path = str(record["file_path"]).strip()

                    if not url or not title or not file_path:
                        errors.append(f"Record {i}: Empty required field")
                        skipped += 1
                        continue

                    # Check for duplicate by URL
                    existing = (
                        session.query(DownloadHistory)
                        .filter(DownloadHistory.url == url)
                        .first()
                    )
                    if existing:
                        errors.append(f"Record {i}: URL already in history")
                        skipped += 1
                        continue

                    # Parse downloaded_at if present
                    downloaded_at = datetime.utcnow()
                    if "downloaded_at" in record:
                        try:
                            if isinstance(record["downloaded_at"], str):
                                downloaded_at = datetime.fromisoformat(
                                    record["downloaded_at"].replace("Z", "+00:00")
                                )
                        except (ValueError, TypeError):
                            pass  # Use default

                    # Create history entry
                    entry = DownloadHistory(
                        url=url,
                        title=title,
                        file_path=file_path,
                        file_size=record.get("file_size"),
                        format_id=record.get("format_id"),
                        duration=record.get("duration"),
                        uploader=record.get("uploader"),
                        downloaded_at=downloaded_at,
                        status=record.get("status", "completed"),
                    )
                    session.add(entry)
                    imported += 1

                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
                    skipped += 1

            session.commit()

        self._logger.info(f"Imported {imported} history entries, skipped {skipped}")

        return ImportResult(
            success=imported > 0 or (imported == 0 and skipped == 0),
            records_imported=imported,
            records_skipped=skipped,
            errors=errors,
            message=f"Imported {imported} history entries, skipped {skipped}",
        )

    def _user_to_dict(self, user: User, fields: list[str]) -> dict[str, Any]:
        """
        Convert a User object to a dictionary with selected fields.

        Parameters
        ----------
        user : User
            User object to convert
        fields : list[str]
            Fields to include

        Returns
        -------
        dict[str, Any]
            Dictionary representation
        """
        full_dict = {
            "id": user.id,
            "name": user.name,
            "preferences": user.preferences_dict,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        return {k: v for k, v in full_dict.items() if k in fields}

    def _history_to_dict(
        self, entry: DownloadHistory, fields: list[str]
    ) -> dict[str, Any]:
        """
        Convert a DownloadHistory object to a dictionary with selected fields.

        Parameters
        ----------
        entry : DownloadHistory
            History entry to convert
        fields : list[str]
            Fields to include

        Returns
        -------
        dict[str, Any]
            Dictionary representation
        """
        full_dict = {
            "id": entry.id,
            "url": entry.url,
            "title": entry.title,
            "file_path": entry.file_path,
            "file_size": entry.file_size,
            "format_id": entry.format_id,
            "duration": entry.duration,
            "uploader": entry.uploader,
            "downloaded_at": (
                entry.downloaded_at.isoformat() if entry.downloaded_at else None
            ),
            "status": entry.status,
            "file_exists": entry.file_exists,
            "thumbnail_url": entry.thumbnail_url,
            "description": entry.description,
        }
        return {k: v for k, v in full_dict.items() if k in fields}

    def _validate_fields(
        self, fields: list[str], valid_fields: list[str], data_type: str
    ) -> None:
        """
        Validate that requested fields are valid.

        Parameters
        ----------
        fields : list[str]
            Fields to validate
        valid_fields : list[str]
            List of valid field names
        data_type : str
            Type of data for error message

        Raises
        ------
        ValidationError
            If invalid fields are requested
        """
        invalid = [f for f in fields if f not in valid_fields]
        if invalid:
            raise ValidationError(
                f"Invalid {data_type} fields: {invalid}. Valid fields: {valid_fields}"
            )
