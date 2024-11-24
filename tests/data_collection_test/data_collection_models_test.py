from data_collection.models import CombinedDatapoint
from flight_data.models import FlightDatapoint
from weather_data.models import WeatherDatapoint
from common.models import Location
import csv
from tempfile import NamedTemporaryFile


def test_combined_datapoint_from_datapoints() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10, 20),
        arrival_airport="JFK",
        arrival_airport_location=Location(20, 20),
        timestamp=0,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )
    weather_datapoint = WeatherDatapoint.empty_from_timestamp(10)

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, weather_datapoint)

    assert combined_datapoint.timestamp == 0
    assert combined_datapoint.flight == flight_datapoint
    assert combined_datapoint.weather == weather_datapoint


def test_combined_datapoint_from_datapoints_with_weather_none() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10, 20),
        arrival_airport="JFK",
        arrival_airport_location=Location(20, 20),
        timestamp=50,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, None)

    assert combined_datapoint.timestamp == 50
    assert combined_datapoint.flight == flight_datapoint
    assert combined_datapoint.weather == WeatherDatapoint.empty_from_timestamp(50)


def test_combined_datapoint_get_attribute_names() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10, 20),
        arrival_airport="JFK",
        arrival_airport_location=Location(20, 20),
        timestamp=0,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )
    weather_datapoint = WeatherDatapoint.empty_from_timestamp(10)

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, weather_datapoint)

    assert combined_datapoint.get_attribute_names() == [
        'timestamp', 'flight_location_latitude', 'flight_location_longitude', 'flight_arrival_airport', 'flight_arrival_airport_location_latitude', 'flight_arrival_airport_location_longitude', 'flight_timestamp', 'flight_horizontal_speed', 'flight_altitude', 'flight_vertical_speed', 'flight_heading', 'flight_distance_to_destination', 'flight_arrival_time', 'flight_time_to_arrival', 'weather_timestamp', 'weather_temperature_celsius', 'weather_feels_like_celsius', 'weather_condition_text', 'weather_wind_speed_kph', 'weather_humidity_percent', 'weather_precipitation_mm', 'weather_visibility_km', 'weather_pressure_mb', 'weather_uv_index'
    ]


def test_combined_datapoint_get_values() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10, 20),
        arrival_airport="JFK",
        arrival_airport_location=Location(20, 20),
        timestamp=20,
        horizontal_speed=5.0,
        altitude=0.2,
        vertical_speed=100.0,
        heading=220.0,
        distance_to_destination=40.0,
        arrival_time=50,
        time_to_arrival=20,
    )
    weather_datapoint = WeatherDatapoint(
        timestamp=10,
        temperature_celsius=5.0,
        feels_like_celsius=5.7,
        condition_text="Cloudy",
        wind_speed_kph=10.0,
        humidity_percent=60.0,
        precipitation_mm=2.0,
        visibility_km=30.0,
        pressure_mb=1020.0,
        uv_index=2.0,
    )

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, weather_datapoint)

    assert combined_datapoint.get_values() == [
        20, 10.0, 20.0, "JFK", 20.0, 20.0, 20, 5.0, 0.2, 100.0, 220.0, 40.0, 50, 20, 10, 5.0, 5.7, "Cloudy", 10.0, 60.0, 2.0, 30.0, 1020.0, 2.0
    ]


def test_combined_datapoint_save_to_csv_with_no_existing_file() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10.0, 20.0),
        arrival_airport="JFK",
        arrival_airport_location=Location(20.0, 20.0),
        timestamp=0,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )
    weather_datapoint = WeatherDatapoint.empty_from_timestamp(10)

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, weather_datapoint)

    with NamedTemporaryFile() as file:
        filename = file.name
        combined_datapoint.save_to_csv(filename)
        with open(filename, mode='r') as f:
            reader = csv.reader(f)
            rows = list(reader)

    assert rows == [
        ['timestamp', 'flight_location_latitude', 'flight_location_longitude', 'flight_arrival_airport', 'flight_arrival_airport_location_latitude', 'flight_arrival_airport_location_longitude', 'flight_timestamp', 'flight_horizontal_speed', 'flight_altitude', 'flight_vertical_speed', 'flight_heading', 'flight_distance_to_destination', 'flight_arrival_time', 'flight_time_to_arrival', 'weather_timestamp', 'weather_temperature_celsius', 'weather_feels_like_celsius', 'weather_condition_text', 'weather_wind_speed_kph', 'weather_humidity_percent', 'weather_precipitation_mm', 'weather_visibility_km', 'weather_pressure_mb', 'weather_uv_index'],
        ['0', '10.0', '20.0', "JFK", '20.0', '20.0', '0', '0.0', '0.0', '0.0', '0.0', '0.0', '0', '0', '10', '0.0', '0.0', "NA", '0.0', '0.0', '0.0', '0.0', '0.0', '0.0'],
    ]


def test_combined_datapoint_save_to_csv_with_already_created_file() -> None:
    flight_datapoint = FlightDatapoint(
        location=Location(10.0, 20.0),
        arrival_airport="JFK",
        arrival_airport_location=Location(20.0, 20.0),
        timestamp=0,
        horizontal_speed=0.0,
        altitude=0.0,
        vertical_speed=0.0,
        heading=0.0,
        distance_to_destination=0.0,
        arrival_time=0,
        time_to_arrival=0,
    )
    weather_datapoint = WeatherDatapoint.empty_from_timestamp(10)

    combined_datapoint = CombinedDatapoint.from_datapoints(flight_datapoint, weather_datapoint)

    with NamedTemporaryFile() as file:
        with open(file.name, mode='w') as f:
            writer = csv.writer(f)
            writer.writerow(['test'])
        filename = file.name
        combined_datapoint.save_to_csv(filename)
        with open(filename, mode='r') as f:
            reader = csv.reader(f)
            rows = list(reader)

    assert rows == [
        ['test'],
        ['0', '10.0', '20.0', "JFK", '20.0', '20.0', '0', '0.0', '0.0', '0.0', '0.0', '0.0', '0', '0', '10', '0.0', '0.0', "NA", '0.0', '0.0', '0.0', '0.0', '0.0', '0.0'],
    ]
