"""Unit tests for export.py feature module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestExportFeature:
    """Tests for ExportFeature class."""

    def test_init(self):
        """Test ExportFeature initialization."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()

        assert feature.name == "Export"

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.export import ExportFeature

        mock_choice.return_value = "back"

        feature = ExportFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.choice_prompt")
    @patch("src.farmer_cli.features.export.text_prompt")
    def test_execute_export_users(self, mock_text, mock_choice, mock_console):
        """Test execute export users option."""
        from src.farmer_cli.features.export import ExportFeature

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_choice.side_effect = ["users", "csv", "back"]
            mock_text.return_value = str(Path(tmpdir) / "export.csv")

            feature = ExportFeature()
            feature.execute()

            mock_console.print.assert_called()

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.choice_prompt")
    @patch("src.farmer_cli.features.export.text_prompt")
    def test_execute_export_history(self, mock_text, mock_choice, mock_console):
        """Test execute export history option."""
        from src.farmer_cli.features.export import ExportFeature

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_choice.side_effect = ["history", "json", "back"]
            mock_text.return_value = str(Path(tmpdir) / "export.json")

            feature = ExportFeature()
            feature.execute()

            mock_console.print.assert_called()

    @patch("src.farmer_cli.features.export.console")
    @patch("src.farmer_cli.features.export.choice_prompt")
    @patch("src.farmer_cli.features.export.text_prompt")
    def test_execute_import_data(self, mock_text, mock_choice, mock_console):
        """Test execute import data option."""
        from src.farmer_cli.features.export import ExportFeature

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test import file
            import_file = Path(tmpdir) / "import.json"
            import_file.write_text('{"users": []}')

            mock_choice.side_effect = ["import", "back"]
            mock_text.return_value = str(import_file)

            feature = ExportFeature()
            feature.execute()

            mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.export import ExportFeature

        feature = ExportFeature()
        # Should not raise
        feature.cleanup()


class TestExportToCSV:
    """Tests for _export_to_csv method."""

    def test_export_to_csv(self):
        """Test exporting to CSV."""
        from src.farmer_cli.features.export import ExportFeature

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.csv"

            feature = ExportFeature()
            data = [
                {"name": "User1", "email": "user1@example.com"},
                {"name": "User2", "email": "user2@example.com"},
            ]

            feature._export_to_csv(data, str(output_path))

            assert output_path.exists()


class TestExportToJSON:
    """Tests for _export_to_json method."""

    def test_export_to_json(self):
        """Test exporting to JSON."""
        from src.farmer_cli.features.export import ExportFeature

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.json"

            feature = ExportFeature()
            data = [
                {"name": "User1", "email": "user1@example.com"},
                {"name": "User2", "email": "user2@example.com"},
            ]

            feature._export_to_json(data, str(output_path))

            assert output_path.exists()
