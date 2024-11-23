import pytest

from common.models import Location


@pytest.mark.parametrize(
    "lat, lon",
    [
        (-91, 0),
        (91, 0),
        (0, -181),
        (0, 181),
    ]
)
def test_location_invalid_input(lat: float, lon: float) -> None:
    with pytest.raises(ValueError):
        Location(lat, lon)


@pytest.mark.parametrize(
    "location1, location2, expected_distance",
    [
        # New York to London
        (Location(40.7128, -74.0060), Location(51.5074, -0.1278), 5570.0),
        # Same point
        (Location(0.0, 0.0), Location(0.0, 0.0), 0.0),
        # Sydney to Tokyo
        (Location(-33.8688, 151.2093), Location(35.6762, 139.6503), 7822.0),
        # Rio de Janeiro to Warsaw
        (Location(-22.908, -43.196), Location(52.237, 21.017), 10404.9),
    ],
)
def test_distance_to(location1: Location, location2: Location, expected_distance: float) -> None:
    dis1 = location1.distance_to(location2)
    dis2 = location2.distance_to(location1)
    assert dis1 == pytest.approx(expected_distance, rel=0.001)
    assert dis2 == pytest.approx(expected_distance, rel=0.001)
    assert dis1 == pytest.approx(dis2, rel=1e-9)


def test_distance_to_is_symmetric() -> None:
    initial_location = Location(0, 0)
    distance = initial_location.distance_to(Location(40, 50))

    assert initial_location.distance_to(Location(-40, 50)) == pytest.approx(distance, rel=1e-9)
    assert initial_location.distance_to(Location(40, -50)) == pytest.approx(distance, rel=1e-9)
    assert initial_location.distance_to(Location(-40, -50)) == pytest.approx(distance, rel=1e-9)
