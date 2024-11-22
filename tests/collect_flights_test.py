from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
import os
import pytest
from freezegun import freeze_time

from config import DOWNLOAD_DATA_DIR
from collect_flights import FlightCollector
from flight_data.flight_data import FlightData
from flight_data.models import FlightDatapoint, FlightInfo

@pytest.fixture
def mock_flight_data() -> MagicMock:
    return MagicMock(spec=FlightData)


@pytest.fixture
def collector(mock_flight_data: MagicMock) -> FlightCollector:
    return FlightCollector(mock_flight_data)


def test_generate_filename(collector: FlightCollector) -> None:
    start = datetime(2024, 1, 1, 10)
    end = datetime(2024, 1, 1, 12)

    filename = collector._generate_filename(start, end)

    assert filename == f'{DOWNLOAD_DATA_DIR}/flights_20240101_1000_to_20240101_1200.csv'


def test_collect_flights_success(collector: FlightCollector, mock_flight_data: MagicMock) -> None:
    mock_flights = [MagicMock(icao24='flight1'), MagicMock(icao24='flight2')]
    mock_flight_data.get_flights.return_value = mock_flights

    start = datetime(2024, 1, 1, 10, 0)
    end = datetime(2024, 1, 1, 12, 0)

    result = collector.collect_flights_in_time_window(start, end)

    assert result == mock_flights
    mock_flight_data.get_flights.assert_called_once_with(
        int(start.timestamp()),
        int(end.timestamp())
    )


def test_collect_flights_no_data(collector: FlightCollector, mock_flight_data: MagicMock) -> None:
    mock_flight_data.get_flights.return_value = None

    start = datetime(2024, 1, 1, 10, 0)
    end = datetime(2024, 1, 1, 12, 0)

    result = collector.collect_flights_in_time_window(start, end)

    assert result is None


def test_process_flights(collector: FlightCollector, mock_flight_data: MagicMock) -> None:
    mock_flights = [MagicMock(icao24='flight1'), MagicMock(icao24='flight2')]
    mock_flight_datapoints = [MagicMock(spec=FlightDatapoint)]
    mock_flight_data.get_flight_datapoints.side_effect = [mock_flight_datapoints, None]

    with patch('collect_flights.save_flight_data_to_csv') as mock_save:
        collector.process_flights(mock_flights, 'test.csv')

    assert mock_flight_data.get_flight_datapoints.call_args_list == [call(mock_flights[0]), call(mock_flights[1])]
    mock_save.assert_called_once_with(mock_flight_datapoints, 'test.csv')


@freeze_time("2024-01-01 12:00:00")
def test_run_raises_error_when_offset_too_big(collector: FlightCollector) -> None:
    collector._generate_filename = MagicMock()
    collector.collect_flights_in_time_window = MagicMock()
    collector.process_flights = MagicMock()
    with pytest.raises(ValueError) as exc:
        collector.run(days_offset=30, hours_offset=0)

    assert str(exc.value) == "Days offset must be less than 30"

    collector._generate_filename.assert_not_called()
    collector.collect_flights_in_time_window.assert_not_called()
    collector.process_flights.assert_not_called()


@pytest.mark.parametrize('hours_offset', [-1, 24, 300])
def test_run_raises_error_when_incorrect_hours_offset(hours_offset: int, collector: FlightCollector) -> None:
    collector._generate_filename = MagicMock()
    collector.collect_flights_in_time_window = MagicMock()
    collector.process_flights = MagicMock()

    with pytest.raises(ValueError) as exc:
        collector.run(days_offset=20, hours_offset=hours_offset)

    assert str(exc.value) == "Hours offset must be between 0 and 24 (excluded)"

    collector._generate_filename.assert_not_called()
    collector.collect_flights_in_time_window.assert_not_called()
    collector.process_flights.assert_not_called()


@pytest.mark.parametrize('hours_offset', [0, 1])
def test_run_doesnt_start_when_end_time_is_after_current_time(hours_offset: int, collector: FlightCollector) -> None:
    collector._generate_filename = MagicMock()
    collector.collect_flights_in_time_window = MagicMock()
    collector.process_flights = MagicMock()

    collector.run(days_offset=0, hours_offset=hours_offset)

    collector._generate_filename.assert_not_called()
    collector.collect_flights_in_time_window.assert_not_called()
    collector.process_flights.assert_not_called()


@freeze_time("2024-01-01 12:00:00")
@pytest.mark.parametrize('flights', [[], None])
def test_run_checks_all_flights_from_offset_to_current_time(flights: None | list[FlightInfo], collector: FlightCollector) -> None:
    current_time = datetime.now()
    collector._generate_filename = MagicMock()
    collector.collect_flights_in_time_window = MagicMock(return_value=flights)
    collector.process_flights = MagicMock()

    collector.run(days_offset=20, hours_offset=0)

    assert collector._generate_filename.call_args_list == [
        call(current_time - timedelta(hours=i), current_time - timedelta(hours=i-2))
        for i in range(20*24, 0, -2)
    ]
    assert collector.collect_flights_in_time_window.call_args_list == [
        call(current_time - timedelta(hours=i), current_time - timedelta(hours=i - 2))
        for i in range(20 * 24, 0, -2)
    ]
    collector.process_flights.assert_not_called()


@freeze_time("2024-01-01 12:00:00")
def test_run_checks_all_flights_from_offset_to_current_time(collector: FlightCollector) -> None:
    mock_flights = [[MagicMock(icao24='flight1'), MagicMock(icao24='flight2')], [MagicMock(icao24='flight3'), MagicMock(icao24='flight4')]]
    output_files = ["file1", "file2"]

    current_time = datetime.now()
    collector._generate_filename = MagicMock(side_effect=output_files)
    collector.collect_flights_in_time_window = MagicMock(side_effect=mock_flights)
    collector.process_flights = MagicMock()

    collector.run(days_offset=0, hours_offset=4)

    assert collector._generate_filename.call_args_list == [
        call(current_time - timedelta(hours=4), current_time - timedelta(hours=2)),
        call(current_time - timedelta(hours=2), current_time),
    ]
    assert collector.collect_flights_in_time_window.call_args_list == [
        call(current_time - timedelta(hours=4), current_time - timedelta(hours=2)),
        call(current_time - timedelta(hours=2), current_time),
    ]
    assert collector.process_flights.call_args_list == [
        call(mock_flights[0], output_files[0]),
        call(mock_flights[1], output_files[1]),
    ]
