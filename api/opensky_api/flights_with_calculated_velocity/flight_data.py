from opensky_api import OpenSkyApi
import time
from airports_data import AirportData
from collections import namedtuple
from utils import haversine_distance, calculate_speed
from dataclasses import dataclass
import yaml


FlightInfo = namedtuple('FlightInfo', ["icao24", "last_seen", "arrival_airport", "call_sign"])
FlightDatapoint = namedtuple('FlightDatapoint', ["latitude", "longitude", "arrival_airport", "arrival_airport_latitude", "arrival_airport_longitude", "time", "horizontal_velocity", "altitude", "vertical_velocity", "heading", "distance_to_destination", "arrival_time", "time_to_arrival"])

@dataclass
class FlightDatapoint:
    latitude: float
    longitude: float
    arrival_airport: str
    arrival_airport_latitude: float
    arrival_airport_longitude: float
    time: int
    horizontal_velocity: float
    altitude: float
    vertical_velocity: float
    heading: float
    distance_to_destination: float
    arrival_time: int
    time_to_arrival: int

    def get_names(self) -> list[str]:
        return list(self.__annotations__.keys())

    def get_values(self) -> list:
        return list(self.__dict__.values())


class FlightData:
    def __init__(self, airports: AirportData):
        with open('credentials.yaml') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        self._api = OpenSkyApi(username= config["open_sky"]['username'], password= config["open_sky"]['password'])
        self._airport_data = airports

    @staticmethod
    def _call_api(func, *args, **kwargs):
        for i in range(5):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Retrying...")
                time.sleep(960)
        raise RuntimeError("Failed to get flight data after 5 attempts.")

    def get_flights(self, start: int, end: int) -> list[FlightInfo] | None:
        data = self._call_api(self._api.get_flights_from_interval, start, end)

        if data is None:
            print("No data returned")
            return None

        flights_info = []
        for flight in data:
            if not self._airport_data.is_airport(flight.estArrivalAirport):
                continue

            flights_info.append(FlightInfo(flight.icao24, flight.lastSeen, flight.estArrivalAirport, flight.callsign and flight.callsign.rstrip(" ")))

        return flights_info

    def get_flight_datapoints(self, flight_info: FlightInfo) -> list[FlightDatapoint] | None:
        flight_data = self._call_api(self._api.get_track_by_aircraft, flight_info.icao24, flight_info.last_seen)
        arrival_airport_location = self._airport_data.get_location(flight_info.arrival_airport)
        if not flight_data:
            print("No data returned")
            return None

        path = flight_data.path
        distances_to_destination = [haversine_distance(datapoint[1], datapoint[2], arrival_airport_location[0], arrival_airport_location[1]) for datapoint in path]
        arrival_time: int | None = None
        for i, datapoint in enumerate(flight_data.path):
            if distances_to_destination[i] < 10:
                arrival_time = datapoint[0]
                distances_to_destination = distances_to_destination[:i + 1]
                path = path[:i + 1]
                break

        if arrival_time is None:
            print("No data points within 10 km of destination")
            return None

        flight_datapoints = []
        last_datapoint = 0
        for i in range(1, len(path)):
            if path[i][0] - path[last_datapoint][0] < 60:
                continue
            flight_datapoints.append(FlightDatapoint(
                path[i][1],
                path[i][2],
                flight_info.arrival_airport,
                arrival_airport_location[0],
                arrival_airport_location[1],
                path[i][0],
                calculate_speed(distances_to_destination[i] - distances_to_destination[last_datapoint], path[i][0] - path[last_datapoint][0]),
                path[i][3],
                calculate_speed((path[i][3] - path[i-1][3]) / 1000, path[i][0] - path[last_datapoint][0]),
                path[i][4],
                distances_to_destination[i],
                arrival_time,
                arrival_time-path[i][0]
            ))
            last_datapoint = i

        return flight_datapoints
