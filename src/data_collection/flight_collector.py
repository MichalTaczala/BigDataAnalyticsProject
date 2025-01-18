from datetime import datetime, timedelta
import structlog
import os

from .models import CombinedDatapoint
from flight_data.flight_data import FlightData, FlightInfo
from flight_data.models import FlightDatapoint
from weather_data.weather_data import WeatherDataProcessor
import config

logger = structlog.get_logger()


class FlightCollector:
    """Collects flight data and save it to CSV"""
    TIME_WINDOW_DELTA = timedelta(hours=2)

    def __init__(self, flight_data: FlightData, output_file_template: str = "flights_{start}_to_{end}.csv") -> None:
        self.flight_data = flight_data
        self.weather_data = WeatherDataProcessor()
        self.output_template = output_file_template

    def _generate_filename(self, start_time: datetime, end_time: datetime) -> str:
        """Generates output filename based on the start and end time of a current time window"""
        start_date_str = start_time.strftime('%Y%m%d_%H%M')
        end_date_str = end_time.strftime('%Y%m%d_%H%M')
        return os.path.join(
            config.DOWNLOAD_DATA_DIR,
            self.output_template.format(start=start_date_str, end=end_date_str),
        )

    def collect_flights_in_time_window(self, start_time: datetime, end_time: datetime) -> list[FlightInfo] | None:
        logger.info("processing time window",
                    start=start_time.isoformat(),
                    end=end_time.isoformat())

        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())

        flights = self.flight_data.get_flights(start_timestamp, end_timestamp)
        if not flights:
            logger.warning("no flights found in time window", start=start_time, end=end_time)
            return None

        logger.info("found flights", count=len(flights))
        return flights

    def process_flights(self, flights: list[FlightInfo], output_file: str) -> None:
        """Convert flights to FlightDatapoints and save them to CSV file"""
        for flight in flights:
            datapoints = self.flight_data.get_flight_datapoints(flight, ignore_min_distance=True)
            if not datapoints:
                logger.warning("missing datapoints", icao24=flight.icao24)
                continue

            combined_datapoints = self.get_weather_data_for_flight_datapoints(datapoints)

            logger.info("saving flight data", datapoints_count=len(datapoints), icao24=flight.icao24)
            for combined_datapoint in combined_datapoints:
                combined_datapoint.save_to_csv(output_file)

    def get_weather_data_for_flight_datapoints(self, flight_datapoints: list[FlightDatapoint]) -> list[CombinedDatapoint]:
        """Get weather data for each flight datapoint and combine datapoint"""
        datapoints: list[CombinedDatapoint] = []
        for flight in flight_datapoints:
            weather_datapoint = self.weather_data.get_weather_datapoint_for_flight_datapoint(flight)
            datapoints.append(CombinedDatapoint.from_datapoints(flight, weather_datapoint))

        return datapoints


    def run(self, days_offset: int, hours_offset: int) -> None:
        """
        Runs the collector for a specified number of days and hours offset from the current time to
        get flight data in batches of 2 hours.
        """
        if days_offset >= 30:
            raise ValueError("Days offset must be less than 30")
        if hours_offset < 0 or hours_offset >= 24:
            raise ValueError("Hours offset must be between 0 and 24 (excluded)")

        current_time = datetime.now()
        start_time = current_time - timedelta(days=days_offset, hours=hours_offset)
        end_time = start_time + self.TIME_WINDOW_DELTA
        while end_time <= current_time:
            output_file = self._generate_filename(start_time, end_time)

            flights = self.collect_flights_in_time_window(start_time, end_time)
            if flights:
                self.process_flights(flights, output_file)

            start_time, end_time = end_time, end_time + self.TIME_WINDOW_DELTA
