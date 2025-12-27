"""Tests for weather.py module."""

from unittest.mock import MagicMock, patch

import pytest


class TestCheckWeather:
    """Tests for check_weather function."""

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.text_prompt")
    @patch("src.farmer_cli.features.weather.fetch_weather")
    @patch("src.farmer_cli.features.weather.display_weather")
    def test_check_weather_success(self, mock_display, mock_fetch, mock_prompt, mock_console):
        """Test successful weather check."""
        from src.farmer_cli.features.weather import check_weather

        mock_prompt.return_value = "London"
        mock_fetch.return_value = {"weather": [{"description": "clear"}], "main": {"temp": 20}}

        check_weather()

        mock_fetch.assert_called_once_with("London")
        mock_display.assert_called_once()

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.text_prompt")
    @patch("src.farmer_cli.features.weather.fetch_weather")
    def test_check_weather_config_error(self, mock_fetch, mock_prompt, mock_console):
        """Test weather check with configuration error."""
        from exceptions import ConfigurationError

        from src.farmer_cli.features.weather import check_weather

        mock_prompt.return_value = "London"
        mock_fetch.side_effect = ConfigurationError("API key not set")

        check_weather()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.text_prompt")
    @patch("src.farmer_cli.features.weather.fetch_weather")
    def test_check_weather_api_error(self, mock_fetch, mock_prompt, mock_console):
        """Test weather check with API error."""
        from exceptions import APIError

        from src.farmer_cli.features.weather import check_weather

        mock_prompt.return_value = "London"
        mock_fetch.side_effect = APIError("API error", status_code=401)

        check_weather()

        mock_console.print.assert_called()

    @patch("src.farmer_cli.features.weather.console")
    @patch("src.farmer_cli.features.weather.text_prompt")
    @patch("src.farmer_cli.features.weather.fetch_weather")
    def test_check_weather_unexpected_error(self, mock_fetch, mock_prompt, mock_console):
        """Test weather check with unexpected error."""
        from src.farmer_cli.features.weather import check_weather

        mock_prompt.return_value = "London"
        mock_fetch.side_effect = Exception("Unexpected error")

        check_weather()

        mock_console.print.assert_called()


class TestFetchWeather:
    """Tests for fetch_weather function."""

    @patch("src.farmer_cli.features.weather.settings")
    def test_fetch_weather_no_api_key(self, mock_settings):
        """Test fetch with no API key."""
        from exceptions import ConfigurationError

        from src.farmer_cli.features.weather import fetch_weather

        mock_settings.openweather_api_key = None

        with pytest.raises(ConfigurationError):
            fetch_weather("London")

    @patch("src.farmer_cli.features.weather.settings")
    @patch("src.farmer_cli.features.weather.requests")
    def test_fetch_weather_success(self, mock_requests, mock_settings):
        """Test successful weather fetch."""
        from src.farmer_cli.features.weather import fetch_weather

        mock_settings.openweather_api_key = "test_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"weather": [{"description": "clear"}], "main": {"temp": 20}}
        mock_requests.get.return_value = mock_response

        result = fetch_weather("London")

        assert result["main"]["temp"] == 20

    @patch("src.farmer_cli.features.weather.settings")
    @patch("src.farmer_cli.features.weather.requests")
    def test_fetch_weather_api_error(self, mock_requests, mock_settings):
        """Test fetch with API error."""
        from src.farmer_cli.features.weather import fetch_weather

        mock_settings.openweather_api_key = "test_key"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "City not found"}
        mock_requests.get.return_value = mock_response

        with pytest.raises(Exception):  # APIError
            fetch_weather("InvalidCity")

    @patch("src.farmer_cli.features.weather.settings")
    @patch("src.farmer_cli.features.weather.requests")
    def test_fetch_weather_network_error(self, mock_requests, mock_settings):
        """Test fetch with network error."""
        import requests
        from exceptions import NetworkError

        from src.farmer_cli.features.weather import fetch_weather

        mock_settings.openweather_api_key = "test_key"
        mock_requests.get.side_effect = requests.RequestException("Network error")
        mock_requests.RequestException = requests.RequestException

        with pytest.raises(NetworkError):
            fetch_weather("London")


class TestDisplayWeather:
    """Tests for display_weather function."""

    @patch("src.farmer_cli.features.weather.console")
    def test_display_weather_full_data(self, mock_console):
        """Test display with full weather data."""
        from src.farmer_cli.features.weather import display_weather

        data = {
            "weather": [{"description": "clear sky"}],
            "main": {
                "temp": 20.5,
                "feels_like": 19.0,
                "humidity": 65,
                "pressure": 1013,
                "temp_min": 18.0,
                "temp_max": 22.0,
            },
            "wind": {"speed": 5.5},
            "clouds": {"all": 10},
        }

        display_weather("London", data)

        assert mock_console.print.call_count >= 5

    @patch("src.farmer_cli.features.weather.console")
    def test_display_weather_minimal_data(self, mock_console):
        """Test display with minimal weather data."""
        from src.farmer_cli.features.weather import display_weather

        data = {
            "weather": [{"description": "cloudy"}],
            "main": {
                "temp": 15.0,
                "feels_like": 14.0,
                "humidity": 80,
                "pressure": 1010,
                "temp_min": 14.0,
                "temp_max": 16.0,
            },
        }

        display_weather("Paris", data)

        mock_console.print.assert_called()
