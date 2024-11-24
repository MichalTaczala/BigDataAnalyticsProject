import pytest
from datetime import datetime
from unittest.mock import MagicMock, call, patch
from typing import Any

from common.models import Location
from weather_data.weather_data import WeatherDataProcessor
from weather_data.models import WeatherDatapoint
from flight_data.models import FlightDatapoint


@pytest.mark.parametrize(
    "weather_data, timestamp, expected_data",
    [
        (
            [
                WeatherDatapoint(0, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(60, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(120, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ],
            60,
            WeatherDatapoint(60, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
        (
            [
                WeatherDatapoint(0, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(60, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(120, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ],
            70,
            WeatherDatapoint(60, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
        (
            [
                WeatherDatapoint(0, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(60, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                WeatherDatapoint(120, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ],
            130,
            WeatherDatapoint(120, 0.0, 0.0, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ),
        (
            None,
            100,
            None,
        )
    ],
)
def test_get_weather_datapoint_for_flight_datapoint(weather_data: list[WeatherDatapoint], timestamp: int, expected_data: WeatherDatapoint | None) -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10, 20),
        arrival_airport="",
        arrival_airport_location=Location(10, 20),
        timestamp=timestamp,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )
    processor = WeatherDataProcessor()
    processor.get_weather_data_for_day = MagicMock(return_value=weather_data)
    with patch("weather_data.weather_data.timestamp_to_date", return_value="2024-03-20") as mock_timestamp_to_date:
        assert processor.get_weather_datapoint_for_flight_datapoint(flight_datapoint) == expected_data

    processor.get_weather_data_for_day.assert_called_once_with(Location(10, 20), "2024-03-20")
    mock_timestamp_to_date.assert_called_once_with(timestamp)


def test_interpolate_hour_range() -> None:
    start_data = {
        "time": "2024-03-20 00:00",
        "temp_c": 0.0,
        "wind_kph": 0.0,
        "humidity": 0.0,
        "precip_mm": 0.0,
        "vis_km": 0.0,
        "pressure_mb": 0.0,
        "feelslike_c": 0.0,
        "uv": 0.0,
        "condition": {
            "text": "Clear",
        },
    }
    end_data = {
        "time": "2024-03-20 01:00",
        "temp_c": 6.0,
        "wind_kph": 0.6,
        "humidity": 60.0,
        "precip_mm": 3.0,
        "vis_km": 1.2,
        "pressure_mb": 600.0,
        "feelslike_c": 12.0,
        "uv": 30.0,
        "condition": {
            "text": "Rain",
        },
    }
    processor = WeatherDataProcessor()
    start_timestamp = int(datetime(2024, 3, 20, 0, 0).timestamp())

    assert processor._interpolate_hour_range(start_data, end_data) == [
        WeatherDatapoint(
            timestamp=start_timestamp + 60 * i,
            temperature_celsius=i/10,
            feels_like_celsius=i/5,
            condition_text="Clear",
            wind_speed_kph=i/100,
            humidity_percent=i,
            precipitation_mm=i/20,
            visibility_km=i/50,
            pressure_mb=i*10,
            uv_index=i/2,
        )
        for i in range(60)
    ]


def test_interpolate_data() -> None:
    data = [
        {"time": f"2024-03-20 00:00"},
        {"time": f"2024-03-20 01:00"},
        {"time": f"2024-03-20 02:00"},
        {"time": f"2024-03-20 03:00"},
    ]
    timestamp = int(datetime(2024, 3, 20, 0, 0).timestamp())

    processor = WeatherDataProcessor()
    processor._interpolate_hour_range = MagicMock(side_effect=[
        [
            WeatherDatapoint.empty_from_timestamp(timestamp),
            WeatherDatapoint.empty_from_timestamp(timestamp + 60),
        ],
        [
            WeatherDatapoint.empty_from_timestamp(timestamp + 3600),
            WeatherDatapoint.empty_from_timestamp(timestamp + 3660),
        ],
        [
            WeatherDatapoint.empty_from_timestamp(timestamp + 7200),
            WeatherDatapoint.empty_from_timestamp(timestamp + 7260),
        ],
    ])

    interpolated_data = processor._interpolate_data(data)

    assert processor._interpolate_hour_range.call_args_list == [
        call(data[0], data[1]),
        call(data[1], data[2]),
        call(data[2], data[3]),
    ]

    assert interpolated_data == [
        WeatherDatapoint.empty_from_timestamp(timestamp),
        WeatherDatapoint.empty_from_timestamp(timestamp + 60),
        WeatherDatapoint.empty_from_timestamp(timestamp + 3600),
        WeatherDatapoint.empty_from_timestamp(timestamp + 3660),
        WeatherDatapoint.empty_from_timestamp(timestamp + 7200),
        WeatherDatapoint.empty_from_timestamp(timestamp + 7260),
    ]


@pytest.mark.parametrize(
    "response_data",
    [
        None,
        {},
        {"fore": ""},
        {"forecast": {}},
        {"forecast": {"forecastday2": []}},
        {"forecast": {"forecastday": []}},
        {"forecast": {"forecastday": [{}]}},
    ]
)
def test_get_weather_data_incorrect_response(response_data: None | dict[str | Any]) -> None:
    processor = WeatherDataProcessor()
    processor._interpolate_data = MagicMock()

    with patch("weather_data.weather_data.fetch_weather_data", return_value=response_data) as mock_fetch_weather_data:
        assert processor.get_weather_data_for_day(Location(0, 0), "2024-03-20") is None

    mock_fetch_weather_data.assert_called_once_with(Location(0, 0), "2024-03-20")
    processor._interpolate_data.assert_not_called()


def test_get_weather_data_success() -> None:
    processor = WeatherDataProcessor()
    processor._interpolate_data = MagicMock(return_value=[WeatherDatapoint.empty_from_timestamp(0)])

    response_data = {"forecast": {"forecastday": [{"hour": [{"timestamp": 123}]}]}}
    with patch("weather_data.weather_data.fetch_weather_data", return_value=response_data) as mock_fetch_weather_data:
        assert processor.get_weather_data_for_day(Location(0, 0), "2024-03-20") == [WeatherDatapoint.empty_from_timestamp(0)]

    mock_fetch_weather_data.assert_called_once_with(Location(0, 0), "2024-03-20")
    processor._interpolate_data.assert_called_once_with([{"timestamp": 123}])
