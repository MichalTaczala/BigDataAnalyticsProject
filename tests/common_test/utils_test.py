import pytest

from common.utils import calculate_speed, interpolate_value, timestamp_to_date


@pytest.mark.parametrize(
    "distance, time, expected_speed",
    [
        (1000.0, 3600.0, 1000.0),
        (0.0, 3600.0, 0.0),
        (-1000.0, 3600.0, 1000.0),
        (10.0, -360.0, 100.0),
        (-2.0, -36.0, 200.0),
        (1000.0, 0.0, None),
        (0.0, 0.0, None),
    ],
)
def test_calculate_speed(distance: float, time: float, expected_speed: float | None) -> None:
    assert calculate_speed(distance, time) == pytest.approx(expected_speed, rel=1e-9)


@pytest.mark.parametrize(
    "start, end, progress, expected_value",
    [
        (0, 1, 0.1, 0.1),
        (2, 4, 0.5, 3.0),
        (10, 0, 0.5, 5.0),
        (0, 0, 0.5, 0.0),
        (0, 1, 0, 0.0),
        (0, 1, 1, 1.0),
    ]
)
def test_interpolate_value(start: float, end: float, progress: float, expected_value: float) -> None:
    assert interpolate_value(start, end, progress) == pytest.approx(expected_value, rel=1e-9)


@pytest.mark.parametrize(
    "timestamp, expected_date",
    [
        (0, "1970-01-01"),
        (1615768400, "2021-03-15"),
        (1672531199, "2022-12-31"),
        (1672531200, "2023-01-01"),
    ],
)
def test_timestamp_to_date(timestamp: int, expected_date: str) -> None:
    assert timestamp_to_date(timestamp) == expected_date
