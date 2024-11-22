from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass
class Location:
    latitude: float  # degrees
    longitude: float  # degrees

    def __post_init__(self) -> None:
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90 degrees, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180 degrees, got {self.longitude}")

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude}"

    def distance_to(self, other: "Location") -> float:
        """Calculates the great-circle distance between two locations"""

        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [self.latitude, self.longitude, other.latitude, other.longitude])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        r = 6371  # Radius of Earth in kilometers

        return c * r
