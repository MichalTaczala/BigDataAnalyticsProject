from dataclasses import dataclass
import os
import csv

from common.models import BaseDataclass
from flight_data.models import FlightDatapoint
from weather_data.models import WeatherDatapoint


@dataclass
class CombinedDatapoint(BaseDataclass):
    timestamp: int
    flight: FlightDatapoint
    weather: WeatherDatapoint

    @classmethod
    def from_datapoints(cls, flight: FlightDatapoint, weather: WeatherDatapoint | None) -> "CombinedDatapoint":
        if weather is None:
            weather = WeatherDatapoint.empty_from_timestamp(flight.timestamp)

        return cls(
            timestamp=flight.timestamp,
            flight=flight,
            weather=weather
        )

    def save_to_csv(self, filename: str) -> None:
        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(self.get_attribute_names())

            writer.writerow(self.get_values())
