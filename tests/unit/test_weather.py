"""Unit tests for weather.py feature module."""

import pytest
from unittest.mock import patch, MagicMock


class TestWeatherFeature:
    """Tests for WeatherFeature class."""

    def test_init(self):
        """Test WeatherFeature initialization."""
        from src.farmer_cli.features.weather import WeatherFeature

        feature = WeatherFeature()

        assert feature.name == "Weather"

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.choice_prompt")
    def test_execute_exit(self, mock_choice, mock_console):
        """Test execute exits on back selection."""
        from src.farmer_cli.features.weather import WeatherFeature

        mock_choice.return_value = "back"

        feature = WeatherFeature()
        feature.execute()

        mock_console.clear.assert_called()

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.choice_prompt")
    @patch("src.farmer_cli.features.weather.text_prompt")
    def test_execute_current_weather(self, mock_text, mock_choice, mock_console):
        """Test execute current weather option."""
        from src.farmer_cli.features.weather import WeatherFeature

        mock_choice.side_effect = ["current", "back"]
        mock_text.return_value = "London"

        feature = WeatherFeature()

        with patch.object(feature, "_get_weather_data", return_value=None):
            feature.execute()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.choice_prompt")
    @patch("src.farmer_cli.features.weather.text_prompt")
    def test_execute_forecast(self, mock_text, mock_choice, mock_console):
        """Test execute forecast option."""
        from src.farmer_cli.features.weather import WeatherFeature

        mock_choice.side_effect = ["forecast", "back"]
        mock_text.return_value = "London"

        feature = WeatherFeature()

        with patch.object(feature, "_get_forecast_data", return_value=None):
            feature.execute()

        mock_console.print.assert_called()

    def test_cleanup(self):
        """Test cleanup method."""
        from src.farmer_cli.features.weather import WeatherFeature

        feature = WeatherFeature()
        # Should not raise
        feature.cleanup()


class TestGetWeatherData:
    """Tests for _get_weather_data method."""

    @patch("src.farmer_cli.features.weather.requests")
    def test_get_weather_data_success(self, mock_requests):
        """Test getting weather data successfully."""
        from src.farmer_cli.features.weather import WeatherFeature

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 20, "humidity": 50},
            "weather": [{"description": "clear sky"}],
            "name": "London"
        }
        mock_requests.get.return_value = mock_response

        feature = WeatherFeature()
        feature.api_key = "test_key"

        result = feature._get_weather_data("London")

        assert result is not None

    @patch("src.farmer_cli.features.weather.requests")
    def test_get_weather_data_no_api_key(self, mock_requests):
        """Test getting weather data without API key."""
        from src.farmer_cli.features.weather import WeatherFeature

        feature = WeatherFeature()
        feature.api_key = None

        result = feature._get_weather_data("London")

        assert result is None

    @patch("src.farmer_cli.features.weather.requests")
    def test_get_weather_data_api_error(self, mock_requests):
        """Test getting weather data with API error."""
        from src.farmer_cli.features.weather import WeatherFeature

        mock_requests.get.side_effect = Exception("API error")

        feature = WeatherFeature()
        feature.api_key = "test_key"

        result = feature._get_weather_data("London")

        assert result is None
