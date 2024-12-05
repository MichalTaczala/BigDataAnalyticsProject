SCHEMA = {
    "type": "record",
    "name": "FlightData",
    "fields": [
        {"name": "latitude", "type": "double"},
        {"name": "longitude", "type": "double"},
        {"name": "arrival_airport", "type": "string"},
        {"name": "arrival_airport_latitude", "type": "double"},
        {"name": "arrival_airport_longitude", "type": "double"},
        {"name": "time", "type": "long"},
        {"name": "horizontal_velocity", "type": "double"},
        {"name": "altitude", "type": "double"},
        {"name": "vertical_velocity", "type": "double"},
        {"name": "heading", "type": "double"},
        {"name": "distance_to_destination", "type": "double"},
        {"name": "arrival_time", "type": "long"},
        {"name": "time_to_arrival", "type": "long"},
        {"name": "temperature", "type": "double"},
        {"name": "feels_like", "type": "double"},
        {"name": "condition", "type": "string"},
        {"name": "wind_speed", "type": "double"},
        {"name": "humidity", "type": "double"},
        {"name": "precipitation", "type": "double"},
        {"name": "visibility", "type": "double"},
        {"name": "pressure", "type": "double"},
        {"name": "uv_index", "type": "double"}
    ]
}