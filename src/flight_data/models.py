from dataclasses import dataclass

from common.models import Location, BaseDataclass


@dataclass
class FlightInfo(BaseDataclass):
    icao24: str
    last_seen: int  # seconds since epoch
    arrival_airport: str
    call_sign: str | None


@dataclass
class FlightDatapoint(BaseDataclass):
    location: Location
    arrival_airport: str
    arrival_airport_location: Location
    timestamp: int  # seconds since epoch
    horizontal_speed: float  # km/h
    altitude: float  # meters
    vertical_speed: float  # km/h
    heading: float  # degrees
    distance_to_destination: float  # km
    arrival_time: int  # seconds since epoch
    time_to_arrival: int  # seconds
