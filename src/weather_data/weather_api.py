import requests
import structlog
from typing import Any
import re

from config import WEATHER_API_KEY, WEATHER_API_URL
from common.models import Location


logger = structlog.get_logger()


def fetch_weather_data(location: Location, date: str) -> dict[str, Any] | None:
    """
    Fetches weather data from the API for a given location and date

    :param location: location of the weather data
    :param date: Date in the format 'YYYY-MM-DD'
    :return: Weather data as dictionary if successful, None otherwise
    """

    if not re.match(r'\d{4}-\d{2}-\d{2}', date):
        raise ValueError("Invalid date format. Please use 'YYYY-MM-DD' format")

    params = {
        'key': WEATHER_API_KEY,
        'q': str(location),
        'dt': date
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        logger.error(f"Error fetching weather data", error=str(e))
        return None
