from dataclasses import dataclass

from common.models import BaseDataclass


@dataclass
class WeatherDatapoint(BaseDataclass):
    """Represents weather conditions at a specific point in time"""
    timestamp: int  # seconds since epoch
    temperature_celsius: float
    feels_like_celsius: float
    condition_text: str
    wind_speed_kph: float
    humidity_percent: float
    precipitation_mm: float
    visibility_km: float
    pressure_mb: float
    uv_index: float

    @classmethod
    def empty_from_timestamp(cls, timestamp: int) -> "WeatherDatapoint":
        """Create an empty WeatherDatapoint with the given timestamp"""
        return cls(
            timestamp=timestamp,
            temperature_celsius=0.0,
            feels_like_celsius=0.0,
            condition_text='NA',
            wind_speed_kph=0.0,
            humidity_percent=0.0,
            precipitation_mm=0.0,
            visibility_km=0.0,
            pressure_mb=0.0,
            uv_index=0.0,
        )
