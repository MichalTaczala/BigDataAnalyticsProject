import pytest

from utils import calculate_speed


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
