"""Unit tests for data_processing.py feature module."""

import pytest
from unittest.mock import patch, MagicMock


class TestDataProcessingFeature:
    """Tests for DataProcessingFeature class."""

    def test_init(self):
        """Test DataProcessingFeature initialization."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()

        assert feature.name == "Data Processing"

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_choice.return_value = "back"

        feature = DataProcessingFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.choice_prompt")
    def test_execute_process_data(self, mock_choice, mock_console):
        """Test execute process data option."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_choice.side_effect = ["process", "back"]

        feature = DataProcessingFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.choice_prompt")
    def test_execute_analyze_data(self, mock_choice, mock_console):
        """Test execute analyze data option."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_choice.side_effect = ["analyze", "back"]

        feature = DataProcessingFeature()
        feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.data_processing.console")
    @patch("src.farmer_cli.features.data_processing.choice_prompt")
    def test_execute_transform_data(self, mock_choice, mock_console):
        """Test execute transform data option."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        mock_choice.side_effect = ["transform", "back"]

        feature = DataProcessingFeature()
        feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.data_processing import DataProcessingFeature

        feature = DataProcessingFeature()
        # Should not raise
        feature.cleanup()
