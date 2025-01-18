from opensky_api import OpenSkyApi
import time
import structlog
from typing import Callable, Any

from .airports_data import AirportData
from common.utils import calculate_speed
from .models import FlightDatapoint, FlightInfo
from config import OPENSKY_PASSWORD, OPENSKY_USERNAME
from common.models import Location

logger = structlog.get_logger()


class FlightData:
    """Class to get flight data from OpenSky API"""
    RETRY_ATTEMPTS = 3  # number of attempts in a row to retry a failed request to OpenSky API
    RETRY_DELAY = 960  # 16 minutes - minimum time between two failed requests to not get blocked
    THRESHOLD_DISTANCE_KM = 10  # threshold distance from destination to consider the plane has arrived

    def __init__(self, airports: AirportData) -> None:
        self._api = OpenSkyApi(username=OPENSKY_USERNAME, password=OPENSKY_PASSWORD)
        self._airport_data = airports

    def _call_api(self, func: Callable, *args, **kwargs) -> Any:
        """
        Wrapper function for error handling and retries for OpenSky API calls.

        :param func: OpenSky API function to call
        :param args: arguments for func
        :param kwargs: keyword arguments for func
        :return: result of func call
        """

        for i in range(self.RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning("An error occurred, retrying..", error=str(e))
                time.sleep(self.RETRY_DELAY)
        raise RuntimeError(f"Failed to get flight data after {self.RETRY_ATTEMPTS} attempts")

    def get_flights(self, start: int, end: int) -> list[FlightInfo] | None:
        """
        Get flights data from OpenSky API for a given time interval.

        :param start: start time in seconds since epoch
        :param end: end time in seconds since epoch
        :return: list of FlightInfo objects or None if no data is found
        """
        data = self._call_api(self._api.get_flights_from_interval, start, end)

        if data is None:
            logger.warning("No flights data returned")
            return None

        flights_info: list[FlightInfo] = []
        for flight in data:
            if not flight.estArrivalAirport:
                continue
            airport = flight.estArrivalAirport.replace(" ", "")
            if not self._airport_data.is_airport(airport):
                continue

            flights_info.append(
                FlightInfo(
                    flight.icao24,
                    flight.lastSeen,
                    airport,
                    flight.callsign and flight.callsign.replace(" ", ""),
                )
            )

        return flights_info

    def get_flight_datapoints(self, flight_info: FlightInfo, ignore_min_distance: bool = False) -> list[FlightDatapoint] | None:
        """Get flight path from OpenSky API for a given flight and convert it to a list of FlightDatapoints"""

        flight_data = self._call_api(self._api.get_track_by_aircraft, flight_info.icao24, flight_info.last_seen)

        if not flight_data:
            logger.info("No flight data found", icao24=flight_info.icao24)
            return None

        arrival_airport_location = self._airport_data.get_location(flight_info.arrival_airport)
        path = flight_data.path  # list of tuples (time, latitude, longitude, altitude, heading, on_ground)
        distances_to_destination = [
            Location(datapoint[1], datapoint[2]).distance_to(arrival_airport_location)
            for datapoint in path
        ]
        arrival_time: int | None = None
        # Calculate arrival time; assume that arrival is when the plane is less than threshold km from the destination
        for i, datapoint in enumerate(flight_data.path):
            if distances_to_destination[i] < self.THRESHOLD_DISTANCE_KM:
                arrival_time = datapoint[0]
                distances_to_destination = distances_to_destination[:i + 1]
                path = path[:i + 1]
                break

        if arrival_time is None and not ignore_min_distance:
            logger.info(f"No data points further than {self.THRESHOLD_DISTANCE_KM} km of destination", icao24=flight_info.icao24)
            return None

        if ignore_min_distance:
            arrival_time = None

        flight_datapoints: list[FlightDatapoint] = []
        last_saved_datapoint = 0
        for i in range(1, len(path)):
            if path[i][0] - path[last_saved_datapoint][0] < 60:  # Skip data points that are less than a minute apart
                continue

            flight_datapoints.append(
                FlightDatapoint(
                    location=Location(latitude=path[i][1], longitude=path[i][2]),
                    arrival_airport=flight_info.arrival_airport,
                    arrival_airport_location=arrival_airport_location,
                    timestamp=path[i][0],
                    horizontal_speed=calculate_speed(
                        distances_to_destination[i] - distances_to_destination[last_saved_datapoint],
                        path[i][0] - path[last_saved_datapoint][0],
                    ),
                    altitude=path[i][3],
                    vertical_speed=calculate_speed(
                        (path[i][3] - path[last_saved_datapoint][3]) / 1000,  # Convert delta in meters to km
                        path[i][0] - path[last_saved_datapoint][0],
                    ),
                    heading=path[i][4],
                    distance_to_destination=distances_to_destination[i],
                    arrival_time=arrival_time,
                    time_to_arrival=arrival_time-path[i][0],
                )
            )
            last_saved_datapoint = i

        return flight_datapoints
