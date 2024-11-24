from typing import Any
from datetime import datetime, timedelta
import structlog

from .weather_api import fetch_weather_data
from common.models import Location
from .models import WeatherDatapoint
from common.utils import interpolate_value, timestamp_to_date
from flight_data.models import FlightDatapoint


logger = structlog.get_logger()


class WeatherDataProcessor:
    """Downloads and processes weather data for a given location and date"""

    DATETIME_FORMAT = '%Y-%m-%d %H:%M'

    def get_weather_datapoint_for_flight_datapoint(self, flight_datapoint: FlightDatapoint) -> WeatherDatapoint | None:
        """
        Retrieves weather data for a given flight data point.

        :param flight_datapoint: Flight data point to get weather data for
        :return: weather data point if there is any closer than 1 minute, None otherwise
        """
        date = timestamp_to_date(flight_datapoint.timestamp)
        weather_data = self.get_weather_data_for_day(flight_datapoint.location, date)

        if not weather_data:
            logger.warning("No weather data found", location=flight_datapoint.location, date=date)
            return None

        lowest_time_delta: float | None = None
        closest_data: WeatherDatapoint | None = None
        for data in weather_data:
            time_delta = abs(data.timestamp - flight_datapoint.timestamp)
            if lowest_time_delta is None or time_delta < lowest_time_delta:
                lowest_time_delta = time_delta
                closest_data = data

        return closest_data

    def get_weather_data_for_day(self, location: Location, date: str) -> list[WeatherDatapoint] | None:
        """
        Retrieves and processes weather data for a given location and date.

        :param location: location of the weather data
        :param date: Date in the format 'YYYY-MM-DD'
        :return: List of weather data points if successful, None otherwise
        """
        raw_data = fetch_weather_data(location, date)
        if (
            not raw_data
            or 'forecast' not in raw_data
            or 'forecastday' not in raw_data['forecast']
            or len(raw_data['forecast']['forecastday']) == 0
            or "hour" not in raw_data['forecast']['forecastday'][0]
        ):
            logger.error("Invalid weather data response", location=location, date=date)
            return None

        hourly_data = raw_data['forecast']['forecastday'][0]['hour']
        return self._interpolate_data(hourly_data)

    def _interpolate_data(self, hourly_data: list[dict[str, Any]]) -> list[WeatherDatapoint]:
        """
        Interpolates hourly weather data into minute-by-minute data

        :param hourly_data: List of hourly weather measurements
        :return: List of minute-by-minute weather data points
        """
        minute_data: list[WeatherDatapoint] = []

        for i in range(len(hourly_data) - 1):
            start_hour = hourly_data[i]
            end_hour = hourly_data[i + 1]

            minute_data.extend(
                self._interpolate_hour_range(start_hour, end_hour)
            )

        return minute_data

    def _interpolate_hour_range(
            self,
            start_hour: dict[str, Any],
            end_hour: dict[str, Any]
    ) -> list[WeatherDatapoint]:
        """
        Interpolates weather data between two hours into minute-by-minute data

        :param start_hour: Weather data at the start of the hour
        :param end_hour: Weather data at the end of the hour
        :return: List of interpolated weather data points for every minute
        """

        start_time = datetime.strptime(start_hour['time'], self.DATETIME_FORMAT)
        end_time = datetime.strptime(end_hour['time'], self.DATETIME_FORMAT)
        delta_minutes = (end_time - start_time).seconds // 60

        interpolated_data: list[WeatherDatapoint] = []

        for minute_offset in range(delta_minutes):
            interpolated_time = start_time + timedelta(minutes=minute_offset)
            progress = minute_offset / delta_minutes

            datapoint = WeatherDatapoint(
                timestamp=int(interpolated_time.timestamp()),
                temperature_celsius=interpolate_value(start_hour['temp_c'], end_hour['temp_c'], progress),
                feels_like_celsius=interpolate_value(start_hour['feelslike_c'], end_hour['feelslike_c'], progress),
                # We cannot easily interpolate text data so we assume that the condition stays the same
                condition_text=start_hour['condition']['text'],
                wind_speed_kph=interpolate_value(start_hour['wind_kph'], end_hour['wind_kph'], progress),
                humidity_percent=interpolate_value(start_hour['humidity'], end_hour['humidity'], progress),
                precipitation_mm=interpolate_value(start_hour['precip_mm'], end_hour['precip_mm'], progress),
                visibility_km=interpolate_value(start_hour['vis_km'], end_hour['vis_km'], progress),
                pressure_mb=interpolate_value(start_hour['pressure_mb'], end_hour['pressure_mb'], progress),
                uv_index=interpolate_value(start_hour['uv'], end_hour['uv'], progress)
            )

            interpolated_data.append(datapoint)

        return interpolated_data
