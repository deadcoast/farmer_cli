"""Tests for export.py feature module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestExportFeature:
    """Tests for ExportFeature class."""

    def test_init(self):
        """Test ExportFeature initialization."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()

        assert feature.name == "Export"
        assert feature._export_service is not None

    @patch("src.farmer_cli.features.export.console")
    def test_execute_csv(self, mock_console):
        """Test execute with csv export type."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.export_users_csv = MagicMock()

        feature.execute(export_type="csv")

        feature.export_users_csv.assert_called_once()

    @patch("src.farmer_cli.features.export.console")
    def test_execute_json(self, mock_console):
        """Test execute with json export type."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.export_users_json = MagicMock()

        feature.execute(export_type="json")

        feature.export_users_json.assert_called_once()


    @patch("src.farmer_cli.features.export.export_help_to_pdf")
    def test_execute_pdf(self, mock_pdf):
        """Test execute with pdf export type."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.execute(export_type="pdf")

        mock_pdf.assert_called_once()

    @patch("src.farmer_cli.features.export.console")
    def test_execute_history_csv(self, mock_console):
        """Test execute with history_csv export type."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.export_history_csv = MagicMock()

        feature.execute(export_type="history_csv")

        feature.export_history_csv.assert_called_once()

    @patch("src.farmer_cli.features.export.console")
    def test_execute_unknown(self, mock_console):
        """Test execute with unknown export type."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.execute(export_type="unknown")

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature.cleanup()  # Should not raise


class TestExportUsersCsv:
    """Tests for export_users_csv method."""

    @patch("src.farmer_cli.features.export.console")
    def test_export_users_csv_success(self, mock_console, tmp_path):
        """Test successful CSV export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        mock_result = ExportResult(
            success=True,
            message="Exported 5 users",
            file_path=tmp_path / "test.csv",
            record_count=5,
            file_size=100,
            format=ExportFormat.CSV,
        )
        feature._export_service.export_users = MagicMock(return_value=mock_result)

        result = feature.export_users_csv(str(tmp_path / "test.csv"))

        assert result is not None
        assert result.success

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.logger")
    def test_export_users_csv_error(self, mock_logger, mock_console, tmp_path):
        """Test CSV export with error."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        feature._export_service.export_users = MagicMock(side_effect=Exception("Test error"))

        result = feature.export_users_csv(str(tmp_path / "test.csv"))

        assert result is None
        mock_console.print.assert_called()


class TestExportUsersJson:
    """Tests for export_users_json method."""

    @patch("src.farmer_cli.features.export.console")
    def test_export_users_json_success(self, mock_console, tmp_path):
        """Test successful JSON export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        mock_result = ExportResult(
            success=True,
            message="Exported 5 users",
            file_path=tmp_path / "test.json",
            record_count=5,
            file_size=100,
            format=ExportFormat.JSON,
        )
        feature._export_service.export_users = MagicMock(return_value=mock_result)

        result = feature.export_users_json(str(tmp_path / "test.json"))

        assert result is not None
        assert result.success


class TestExportHistoryCsv:
    """Tests for export_history_csv method."""

    @patch("src.farmer_cli.features.export.console")
    def test_export_history_csv_success(self, mock_console, tmp_path):
        """Test successful history CSV export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        mock_result = ExportResult(
            success=True,
            message="Exported 10 records",
            file_path=tmp_path / "history.csv",
            record_count=10,
            file_size=200,
            format=ExportFormat.CSV,
        )
        feature._export_service.export_history = MagicMock(return_value=mock_result)

        result = feature.export_history_csv(str(tmp_path / "history.csv"))

        assert result is not None
        assert result.success


class TestExportHistoryJson:
    """Tests for export_history_json method."""

    @patch("src.farmer_cli.features.export.console")
    def test_export_history_json_success(self, mock_console, tmp_path):
        """Test successful history JSON export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        mock_result = ExportResult(
            success=True,
            message="Exported 10 records",
            file_path=tmp_path / "history.json",
            record_count=10,
            file_size=200,
            format=ExportFormat.JSON,
        )
        feature._export_service.export_history = MagicMock(return_value=mock_result)

        result = feature.export_history_json(str(tmp_path / "history.json"))

        assert result is not None


class TestExportHistoryPdf:
    """Tests for export_history_pdf method."""

    @patch("src.farmer_cli.features.export.console")
    def test_export_history_pdf_success(self, mock_console, tmp_path):
        """Test successful history PDF export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        mock_result = ExportResult(
            success=True,
            message="Exported 10 records",
            file_path=tmp_path / "history.pdf",
            record_count=10,
            file_size=500,
            format=ExportFormat.PDF,
        )
        feature._export_service.export_history = MagicMock(return_value=mock_result)

        result = feature.export_history_pdf(str(tmp_path / "history.pdf"))

        assert result is not None


class TestReportExportResult:
    """Tests for _report_export_result method."""

    @patch("src.farmer_cli.features.export.console")
    def test_report_success_with_records(self, mock_console, tmp_path):
        """Test reporting successful export with records."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        result = ExportResult(
            success=True,
            message="Exported 5 users",
            file_path=tmp_path / "test.csv",
            record_count=5,
            file_size=100,
            format=ExportFormat.CSV,
        )

        feature._report_export_result(result)

        assert mock_console.print.call_count >= 3

    @patch("src.farmer_cli.features.export.console")
    def test_report_success_no_records(self, mock_console, tmp_path):
        """Test reporting successful export with no records."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        result = ExportResult(
            success=True,
            message="No records to export",
            file_path=tmp_path / "test.csv",
            record_count=0,
            file_size=0,
            format=ExportFormat.CSV,
        )

        feature._report_export_result(result)

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.export.console")
    def test_report_failure(self, mock_console, tmp_path):
        """Test reporting failed export."""
        from src.farmer_cli.features.export import ExportFeature
        from src.farmer_cli.services.export import ExportFormat, ExportResult

        feature = ExportFeature()
        result = ExportResult(
            success=False,
            message="Export failed",
            file_path=tmp_path / "test.csv",
            record_count=0,
            file_size=0,
            format=ExportFormat.CSV,
        )

        feature._report_export_result(result)

        mock_console.print.assert_called()


class TestExportUsersToCsv:
    """Tests for export_users_to_csv function."""

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.get_session")
    def test_export_users_to_csv_no_users(self, mock_session, mock_console):
        """Test export with no users."""
        from src.farmer_cli.features.export import export_users_to_csv

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.query.return_value.order_by.return_value.all.return_value = []
        mock_session.return_value = mock_ctx

        export_users_to_csv()

        mock_console.print.assert_called()


class TestGenerateHelpHtml:
    """Tests for generate_help_html function."""

    def test_generate_help_html(self):
        """Test HTML generation."""
        from src.farmer_cli.features.export import generate_help_html

        html = generate_help_html()

        assert "<!DOCTYPE html>" in html
        assert "Help Documentation" in html
        assert "Data Processing" in html
