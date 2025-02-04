from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


class BaseDataclass:
    """Base class for dataclasses that provides methods for getting attribute names and values recursively"""
    def get_attribute_names(self) -> list[str]:
        """
        Recursively gets all attribute names of the dataclass and its nested dataclasses

        If an attribute is an object which is a child of BaseDataclass, the attribute names of the child object
        will be prefixed with the parent attribute name and an underscore.
        """
        keys: list[str] = []
        for key, value in zip(self.__annotations__.keys(), self.__dict__.values()):
            if isinstance(value, BaseDataclass):
                keys.extend(
                    [f"{key}_{sub_key}" for sub_key in value.get_attribute_names()]
                )
            else:
                keys.append(key)
        return keys

    def get_values(self) -> list:
        """Recursively gets all attribute values of the dataclass and its nested dataclasses"""
        values = []
        for value in self.__dict__.values():
            if isinstance(value, BaseDataclass):
                values.extend(value.get_values())
            else:
                values.append(value)
        return values


@dataclass
class Location(BaseDataclass):
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
