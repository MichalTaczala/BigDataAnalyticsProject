from dataclasses import dataclass

from common_models import Location


@dataclass
class FlightInfo:
    icao24: str
    last_seen: int  # seconds since epoch
    arrival_airport: str
    call_sign: str | None


@dataclass
class FlightDatapoint:
    location: Location
    arrival_airport: str
    arrival_airport_location: Location
    time: int  # seconds since epoch
    horizontal_speed: float  # km/h
    altitude: float  # meters
    vertical_speed: float  # km/h
    heading: float  # degrees
    distance_to_destination: float  # km
    arrival_time: int  # seconds since epoch
    time_to_arrival: int  # seconds

    def get_attribute_names(self) -> list[str]:
        return list(self.__annotations__.keys())

    def get_values(self) -> list:
        return list(self.__dict__.values())
