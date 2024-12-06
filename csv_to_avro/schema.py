schema = {
    "type": "record",
    "name": "FlightWeatherData",
    "fields": [
        {"name": "timestamp", "type": "long"},
        {"name": "flight_location_latitude", "type": "double"},
        {"name": "flight_location_longitude", "type": "double"},
        {"name": "flight_arrival_airport", "type": "string"},
        {"name": "flight_arrival_airport_location_latitude", "type": "double"},
        {"name": "flight_arrival_airport_location_longitude", "type": "double"},
        {"name": "flight_timestamp", "type": "long"},
        {"name": "flight_horizontal_speed", "type": "double"},
        {"name": "flight_altitude", "type": "double"},
        {"name": "flight_vertical_speed", "type": "double"},
        {"name": "flight_heading", "type": "double"},
        {"name": "flight_distance_to_destination", "type": "double"},
        {"name": "flight_arrival_time", "type": "long"},
        {"name": "flight_time_to_arrival", "type": "long"},
        {"name": "weather_timestamp", "type": "long"},
        {"name": "weather_temperature_celsius", "type": "double"},
        {"name": "weather_feels_like_celsius", "type": "double"},
        {"name": "weather_condition_text", "type": "string"},
        {"name": "weather_wind_speed_kph", "type": "double"},
        {"name": "weather_humidity_percent", "type": "double"},
        {"name": "weather_precipitation_mm", "type": "double"},
        {"name": "weather_visibility_km", "type": "double"},
        {"name": "weather_pressure_mb", "type": "double"},
        {"name": "weather_uv_index", "type": "double"}
    ]
}
