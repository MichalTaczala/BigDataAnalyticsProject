from unittest.mock import MagicMock, patch, call
import pytest
from typing import Generator
from opensky_api import FlightData as OpenSkyFlightData

from flight_data.airports_data import AirportData
from flight_data.flight_data import FlightData
from flight_data.models import FlightInfo
from config import OPENSKY_PASSWORD, OPENSKY_USERNAME
from common.models import Location


@pytest.fixture
def mock_airports_data() -> MagicMock:
    mock = MagicMock(spec=AirportData)
    mock.is_airport.side_effect = lambda code: code != "INVALID"
    mock.get_location.return_value = Location(10, 5)
    return mock


@pytest.fixture
def mock_opensky_api() -> Generator[MagicMock, None, None]:
    with patch("flight_data.flight_data.OpenSkyApi") as mock:
        yield mock


@pytest.fixture
def flight_data(mock_airports_data: MagicMock, mock_opensky_api: MagicMock) -> FlightData:
    flight_data = FlightData(mock_airports_data)
    mock_opensky_api.assert_called_once_with(username=OPENSKY_USERNAME, password=OPENSKY_PASSWORD)
    return flight_data


def test_call_api_success(flight_data: FlightData, mock_opensky_api: MagicMock) -> None:
    with patch("flight_data.flight_data.time.sleep") as mock_sleep:
        flight_data._call_api(mock_opensky_api.get_flights_from_interval, "abc", test="def")

    mock_opensky_api.get_flights_from_interval.assert_called_once_with("abc", test="def")
    mock_sleep.assert_not_called()


def test_call_api_success_after_second_attempt(flight_data: FlightData, mock_opensky_api: MagicMock) -> None:
    mock_opensky_api.get_flights_from_interval.side_effect = [RuntimeError, "success"]
    with patch("flight_data.flight_data.time.sleep") as mock_sleep:
        flight_data._call_api(mock_opensky_api.get_flights_from_interval, "abc", test="def")

    assert mock_opensky_api.get_flights_from_interval.call_args_list == [
        call("abc", test="def"),
        call("abc", test="def"),
    ]
    mock_sleep.assert_called_once_with(960)


def test_call_api_raises_error(flight_data: FlightData, mock_opensky_api: MagicMock) -> None:
    mock_opensky_api.get_flights_from_interval.side_effect = RuntimeError
    with patch("flight_data.flight_data.time.sleep") as mock_sleep, pytest.raises(RuntimeError) as exc:
        flight_data._call_api(mock_opensky_api.get_flights_from_interval, "abc", test="def")

    assert mock_opensky_api.get_flights_from_interval.call_args_list == [
        call("abc", test="def"),
        call("abc", test="def"),
        call("abc", test="def"),
    ]
    assert mock_sleep.call_args_list == [call(960), call(960), call(960)]
    assert str(exc.value) == "Failed to get flight data after 3 attempts"


def test_get_flights_success(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    raw_flight_info = [
        OpenSkyFlightData(
            ["flight1", 0, "", 1635728300, "JFK", "ABC123", 0, 0, 0, 0, 0, 0]
        ),
        # Remove excessive spaces
        OpenSkyFlightData(
            ["flight2", 0, "", 1635728400, "L  AX   ", "D EF4 56 ", 0, 0, 0, 0, 0, 0]
        ),
        # Handle none call sign
        OpenSkyFlightData(
            ["flight3", 0, "", 1635728500, "WSH", None, 0, 0, 0, 0, 0, 0]
        ),
        # Remove because of invalid airport code
        OpenSkyFlightData(
            ["flight4", 0, "", 1635728600, "INVALID", "GHI222", 0, 0, 0, 0, 0, 0]
        ),
        # Remove because of not airport code
        OpenSkyFlightData(
            ["flight4", 0, "", 1635728600, None, "GHI222", 0, 0, 0, 0, 0, 0]
        ),
    ]
    expected_results = [
        FlightInfo(
            icao24="flight1",
            arrival_airport="JFK",
            last_seen=1635728300,
            call_sign="ABC123",
        ),
        FlightInfo(
            icao24="flight2",
            arrival_airport="LAX",
            last_seen=1635728400,
            call_sign="DEF456",
        ),
        FlightInfo(
            icao24="flight3",
            arrival_airport="WSH",
            last_seen=1635728500,
            call_sign=None,
        ),
    ]
    flight_data._call_api = MagicMock(return_value=raw_flight_info)
    flights = flight_data.get_flights(1, 2)

    assert flights == expected_results
    flight_data._call_api.assert_called_once_with(flight_data._api.get_flights_from_interval, 1, 2)
    assert mock_airports_data.is_airport.call_args_list == [
        call("JFK"),
        call("LAX"),
        call("WSH"),
        call("INVALID"),
    ]


def test_get_flights_no_data(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    flight_data._call_api = MagicMock(return_value=None)
    flights = flight_data.get_flights(1, 2)

    assert flights is None
    flight_data._call_api.assert_called_once_with(flight_data._api.get_flights_from_interval, 1, 2)
    mock_airports_data.is_airport.assert_not_called()



def test_get_flight_datapoints_no_data(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    flight_data._call_api = MagicMock(return_value=None)
    flight_info = FlightInfo("flight1", 1635728300, "JFK", "ABC123")
    datapoints = flight_data.get_flight_datapoints(flight_info)

    assert datapoints is None
    flight_data._call_api.assert_called_once_with(flight_data._api.get_track_by_aircraft, "flight1", 1635728300)
    mock_airports_data.get_location.assert_not_called()


def test_get_flight_datapoints_arrival_time_too_big_distance_to_destination(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    raw_flight_data = MagicMock(path=[(1635728300, 0, 0, 0, 0, False), (1635728400, 0, 1, 0, 0, False)])
    flight_data._call_api = MagicMock(return_value=raw_flight_data)
    flight_info = FlightInfo("flight1", 1635728300, "JFK", "ABC123")
    with patch("flight_data.flight_data.Location.distance_to") as mock_distance_to:
        mock_distance_to.return_value = 50
        datapoints = flight_data.get_flight_datapoints(flight_info)

    assert datapoints is None
    flight_data._call_api.assert_called_once_with(flight_data._api.get_track_by_aircraft, "flight1", 1635728300)
    mock_airports_data.get_location.assert_called_once_with("JFK")
    assert mock_distance_to.call_args_list == [
        call(Location(10, 5)),
        call(Location(10, 5)),
    ]


def test_get_flight_datapoints_success(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    raw_flight_data = MagicMock(path=[(1635728300, 0, 0, 100, 0, False), (1635728400, 0, 1, 50, 20, False), (1635728500, 1, 1, 0, 30, False)])
    flight_data._call_api = MagicMock(return_value=raw_flight_data)
    flight_info = FlightInfo("flight1", 1635728300, "JFK", "ABC123")
    with patch("flight_data.flight_data.Location.distance_to") as mock_distance_to:
        mock_distance_to.side_effect = [30, 15, 5]
        datapoints = flight_data.get_flight_datapoints(flight_info)

    assert len(datapoints) == 2
    assert datapoints[0].timestamp == 1635728400
    assert datapoints[0].location == Location(0, 1)
    assert datapoints[0].arrival_airport == "JFK"
    assert datapoints[0].arrival_airport_location == Location(10, 5)
    assert datapoints[0].horizontal_speed == pytest.approx(15 * 36, rel=1e-9)
    assert datapoints[0].altitude == 50
    assert datapoints[0].vertical_speed == pytest.approx(0.05 * 36, rel=1e-9)
    assert datapoints[0].heading == 20
    assert datapoints[0].distance_to_destination == 15
    assert datapoints[0].arrival_time == 1635728500
    assert datapoints[0].time_to_arrival == 100

    assert datapoints[1].timestamp == 1635728500
    assert datapoints[1].location == Location(1, 1)
    assert datapoints[1].arrival_airport == "JFK"
    assert datapoints[1].arrival_airport_location == Location(10, 5)
    assert datapoints[1].horizontal_speed == pytest.approx(10 * 36, rel=1e-9)
    assert datapoints[1].altitude == 0
    assert datapoints[1].vertical_speed == pytest.approx(0.05 * 36, rel=1e-9)
    assert datapoints[1].heading == 30
    assert datapoints[1].distance_to_destination == 5
    assert datapoints[1].arrival_time == 1635728500
    assert datapoints[1].time_to_arrival == 0

    flight_data._call_api.assert_called_once_with(flight_data._api.get_track_by_aircraft, "flight1", 1635728300)
    mock_airports_data.get_location.assert_called_once_with("JFK")
    assert mock_distance_to.call_args_list == [
        call(Location(10, 5)),
        call(Location(10, 5)),
        call(Location(10, 5)),
    ]


def test_get_flight_datapoints_success_with_skip(flight_data: FlightData, mock_airports_data: MagicMock) -> None:
    raw_flight_data = MagicMock(
        path=[(1635728300, 0, 0, 100, 0, False), (1635728350, 0, 0.5, 90, 10, False), (1635728400, 0, 1, 50, 20, False), (1635728500, 1, 1, 0, 30, False)])
    flight_data._call_api = MagicMock(return_value=raw_flight_data)
    flight_info = FlightInfo("flight1", 1635728300, "JFK", "ABC123")
    with patch("flight_data.flight_data.Location.distance_to") as mock_distance_to:
        mock_distance_to.side_effect = [30, 25, 15, 5]
        datapoints = flight_data.get_flight_datapoints(flight_info)

    assert len(datapoints) == 2
    assert datapoints[0].timestamp == 1635728400
    assert datapoints[0].location == Location(0, 1)
    assert datapoints[0].arrival_airport == "JFK"
    assert datapoints[0].arrival_airport_location == Location(10, 5)
    assert datapoints[0].horizontal_speed == pytest.approx(15 * 36, rel=1e-9)
    assert datapoints[0].altitude == 50
    assert datapoints[0].vertical_speed == pytest.approx(0.05 * 36, rel=1e-9)
    assert datapoints[0].heading == 20
    assert datapoints[0].distance_to_destination == 15
    assert datapoints[0].arrival_time == 1635728500
    assert datapoints[0].time_to_arrival == 100

    assert datapoints[1].timestamp == 1635728500
    assert datapoints[1].location == Location(1, 1)
    assert datapoints[1].arrival_airport == "JFK"
    assert datapoints[1].arrival_airport_location == Location(10, 5)
    assert datapoints[1].horizontal_speed == pytest.approx(10 * 36, rel=1e-9)
    assert datapoints[1].altitude == 0
    assert datapoints[1].vertical_speed == pytest.approx(0.05 * 36, rel=1e-9)
    assert datapoints[1].heading == 30
    assert datapoints[1].distance_to_destination == 5
    assert datapoints[1].arrival_time == 1635728500
    assert datapoints[1].time_to_arrival == 0

    flight_data._call_api.assert_called_once_with(flight_data._api.get_track_by_aircraft, "flight1", 1635728300)
    mock_airports_data.get_location.assert_called_once_with("JFK")
    assert mock_distance_to.call_args_list == [
        call(Location(10, 5)),
        call(Location(10, 5)),
        call(Location(10, 5)),
        call(Location(10, 5)),
    ]
