import pytest
import requests
from requests_mock.mocker import Mocker

from weather_data.weather_api import fetch_weather_data
from common.models import Location
from config import WEATHER_API_KEY, WEATHER_API_URL


@pytest.mark.parametrize(
    "date",
    [
        "202-01-01",
        "2021-2-01",
        "2021-03-1",
        "20210301",
        "2021-0301",
        "01-01-2021",
        "01-2021-01",
    ]
)
def test_fetch_weather_data_raises_error_for_invalid_date_format(date: str, requests_mock: Mocker) -> None:
    location = Location(0, 0)

    with pytest.raises(ValueError) as e:
        fetch_weather_data(location, date)

    assert str(e.value) == "Invalid date format. Please use 'YYYY-MM-DD' format"
    assert requests_mock.called is False


def test_fetch_weather_data_successful(requests_mock: Mocker) -> None:
    location = Location(51.5074, -0.1278)
    date = "2024-03-20"

    requests_mock.get(
        WEATHER_API_URL,
        json={"test": "data"},
    )

    result = fetch_weather_data(location, date)

    assert result is not None
    assert result == {"test": "data"}
    assert requests_mock.called
    assert requests_mock.call_count == 1

    last_request = requests_mock.last_request
    assert f'key={WEATHER_API_KEY}' in last_request.url
    assert f'q={location}'.replace(",", "%2C") in last_request.url
    assert f'dt={date}' in last_request.url


def test_fetch_weather_data_failed_request_returns_none(requests_mock: Mocker) -> None:
    location = Location(51.5074, -0.1278)
    date = "2024-03-20"

    requests_mock.get(
        WEATHER_API_URL,
        status_code=404,
    )

    result = fetch_weather_data(location, date)

    assert result is None


def test_fetch_weather_data_invalid_json_response_returns_none(requests_mock: Mocker) -> None:
    location = Location(51.5074, -0.1278)
    date = "2024-03-20"

    requests_mock.get(
        WEATHER_API_URL,
        text="Invalid JSON",
    )

    result = fetch_weather_data(location, date)

    assert result is None


@pytest.mark.parametrize("exception", [
    requests.ConnectionError("Connection failed"),
    requests.Timeout("Request timed out"),
    requests.RequestException("Generic request exception")
])
def test_request_exceptions_return_none(requests_mock: Mocker, exception: requests.RequestException):
    location = Location(51.5074, -0.1278)
    date = "2024-03-20"

    requests_mock.get(
        WEATHER_API_URL,
        exc=exception,
    )

    result = fetch_weather_data(location, date)

    assert result is None
