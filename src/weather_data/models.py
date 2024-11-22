from dataclasses import dataclass


@dataclass
class WeatherDatapoint:
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
