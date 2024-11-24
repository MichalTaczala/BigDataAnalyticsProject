import pytest


from flight_data.models import FlightDatapoint
from common.models import Location


@pytest.fixture
def sample_flight() -> FlightDatapoint:
    return FlightDatapoint(
        location=Location(40.7128, -74.0060),
        arrival_airport="JFK",
        arrival_airport_location=Location(40.6413, -73.7781),
        timestamp=1635724800,
        horizontal_speed=250.5,
        altitude=35000.0,
        vertical_speed=-2.5,
        heading=90.0,
        distance_to_destination=150.3,
        arrival_time=1635728400,
        time_to_arrival=3600
    )


def test_get_attribute_names(sample_flight: FlightDatapoint) -> None:
    expected_names = [
        'location_latitude', 'location_longitude', 'arrival_airport', 'arrival_airport_location_latitude', 'arrival_airport_location_longitude', 'timestamp', 'horizontal_speed', 'altitude',
        'vertical_speed', 'heading', 'distance_to_destination', 'arrival_time',
        'time_to_arrival'
    ]
    assert sample_flight.get_attribute_names() == expected_names
    assert len(sample_flight.get_attribute_names()) == 13


def test_get_values(sample_flight):
    expected_values = [
        40.7128, -74.0060, "JFK", 40.6413, -73.7781, 1635724800,
        250.5, 35000.0, -2.5, 90.0, 150.3, 1635728400, 3600
    ]
    assert sample_flight.get_values() == expected_values
    assert len(sample_flight.get_values()) == 13
    assert isinstance(sample_flight.get_values(), list)
