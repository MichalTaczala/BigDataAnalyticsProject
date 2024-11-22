import pytest

from flight_data.airports_data import AirportData
from common_models import Location


@pytest.fixture
def airports_data() -> AirportData:
    return AirportData("tests/flight_data_test/airports-test.csv")


@pytest.mark.parametrize(
    "icao, expected",
    [
        ("KA34", True),
        ("KAAA", True),
        ("KAAF", True),
        ("XXXX", False),
        ("YYYY", False),
        ("AAAA", False),
    ]
)
def test_is_airport(airports_data: AirportData, icao: str, expected: bool) -> None:
    assert airports_data.is_airport(icao) == expected


@pytest.mark.parametrize(
    "icao, expected",
    [
        ("KA34", Location(39.238581, -119.555023)),
        ("KAAA", Location(40.158699, -89.334999)),
        ("KAAF", Location(29.727501, -85.027496)),
    ]
)
def test_get_location(airports_data: AirportData, icao: str, expected: Location) -> None:
    assert airports_data.get_location(icao) == expected
