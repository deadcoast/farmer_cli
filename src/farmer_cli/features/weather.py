"""
Weather feature for Farmer CLI.

This module provides weather checking functionality using
the OpenWeatherMap API.
"""

import logging

import requests

from config.settings import settings
from exceptions import APIError
from exceptions import ConfigurationError
from exceptions import NetworkError

from ..core.constants import API_TIMEOUT
from ..ui.console import console
from ..ui.prompts import text_prompt


logger = logging.getLogger(__name__)


def check_weather() -> None:
    """Check weather for a city."""
    console.clear()
    console.print("[bold cyan]Weather Check[/bold cyan]\n")

    city = text_prompt(
        "Enter city name", validator=lambda x: bool(x.strip()), error_message="City name cannot be empty"
    )

    try:
        weather_data = fetch_weather(city)
        display_weather(city, weather_data)
    except (ConfigurationError, APIError, NetworkError) as e:
        console.print(f"[bold red]{e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        logger.error(f"Unexpected error in weather check: {e}")

    console.input("\nPress Enter to return...")


def fetch_weather(city: str) -> dict:
    """
    Fetch weather data from OpenWeatherMap API.

    Args:
        city: City name

    Returns:
        Weather data dictionary

    Raises:
        ConfigurationError: If API key not configured
        APIError: If API request fails
        NetworkError: If network request fails
    """
    api_key = settings.openweather_api_key
    if not api_key:
        raise ConfigurationError("OpenWeather API key not configured. Please set OPENWEATHER_API_KEY in .env file.")

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get("message", "Failed to fetch weather data")
            raise APIError(f"Weather API error: {error_msg}", status_code=response.status_code)

        return data

    except requests.RequestException as e:
        raise NetworkError(f"Network error: {e}") from e


def display_weather(city: str, data: dict) -> None:
    """
    Display weather information.

    Args:
        city: City name
        data: Weather data from API
    """
    # Extract weather information
    weather = data["weather"][0]
    main = data["main"]
    wind = data.get("wind", {})
    clouds = data.get("clouds", {})

    # Display formatted weather
    console.print(f"\n[bold yellow]Weather for {city.title()}[/bold yellow]\n")

    # Main weather info
    console.print(f"[bold]Conditions:[/bold] {weather['description'].capitalize()}")
    console.print(f"[bold]Temperature:[/bold] {main['temp']:.1f}°C")
    console.print(f"[bold]Feels Like:[/bold] {main['feels_like']:.1f}°C")
    console.print(f"[bold]Humidity:[/bold] {main['humidity']}%")
    console.print(f"[bold]Pressure:[/bold] {main['pressure']} hPa")

    # Additional info
    if wind:
        console.print(f"[bold]Wind Speed:[/bold] {wind.get('speed', 0)} m/s")
    if clouds:
        console.print(f"[bold]Cloud Cover:[/bold] {clouds.get('all', 0)}%")

    # Temperature range
    console.print(f"\n[dim]Min: {main['temp_min']:.1f}°C | Max: {main['temp_max']:.1f}°C[/dim]")
