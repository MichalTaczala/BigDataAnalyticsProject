import fastavro
import csv
import os
import argparse
from pathlib import Path

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


def detect_csv_format(header):
    old_format_indicators = ["latitude", "longitude", "arrival_airport", "Temperature(°C)"]
    new_format_indicators = ["flight_location_latitude", "flight_location_longitude", "weather_temperature_celsius"]

    old_matches = sum(
        1 for indicator in old_format_indicators if any(indicator.lower() in col.lower() for col in header))
    new_matches = sum(
        1 for indicator in new_format_indicators if any(indicator.lower() in col.lower() for col in header))

    return "old" if old_matches > new_matches else "new"


def get_field_mappings(header, csv_format):
    if csv_format == "new":
        return {i: field.lower() for i, field in enumerate(header)}

    # Mapping for old format
    old_format_mapping = {
        "latitude": "flight_location_latitude",
        "longitude": "flight_location_longitude",
        "arrival_airport": "flight_arrival_airport",
        "arrival_airport_latitude": "flight_arrival_airport_location_latitude",
        "arrival_airport_longitude": "flight_arrival_airport_location_longitude",
        "time": ["timestamp", "flight_timestamp", "weather_timestamp"],  # Map time to both fields
        "horizontal_velocity": "flight_horizontal_speed",
        "altitude": "flight_altitude",
        "vertical_velocity": "flight_vertical_speed",
        "heading": "flight_heading",
        "distance_to_destination": "flight_distance_to_destination",
        "arrival_time": "flight_arrival_time",
        "time_to_arrival": "flight_time_to_arrival",
        "temperature(c)": "weather_temperature_celsius",
        "feels like(c)": "weather_feels_like_celsius",
        "condition": "weather_condition_text",
        "wind speed(kph)": "weather_wind_speed_kph",
        "humidity(%)": "weather_humidity_percent",
        "precipitation(mm)": "weather_precipitation_mm",
        "visibility(km)": "weather_visibility_km",
        "pressure(mb)": "weather_pressure_mb",
        "uv index": "weather_uv_index"
    }

    print(header)
    return {i: old_format_mapping[col.replace("Â°", "").lower()] for i, col in enumerate(header)
            if col.replace("Â°", "").lower() in old_format_mapping}


def convert_csv_to_avro(input_file, output_file):
    records = []
    with open(input_file, 'r', encoding='latin-1') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)

        csv_format = detect_csv_format(header)
        field_mappings = get_field_mappings(header, csv_format)
        for row in reader:
            try:
                record = {}
                for index, value in enumerate(row):
                    if index in field_mappings:
                        field_names = field_mappings[index]
                        if isinstance(field_names, list):
                            # Handle multiple field mappings (for time field)
                            for field_name in field_names:
                                record[field_name] = int(float(value))
                        else:
                            field_name = field_names
                            if field_name in ["flight_arrival_airport", "weather_condition_text"]:
                                record[field_name] = value
                            else:
                                record[field_name] = float(value)
                                if "timestamp" in field_name or "time" in field_name:
                                    record[field_name] = int(float(value))

                # Set weather_timestamp for old format
                if csv_format == "old":
                    record["weather_timestamp"] = record["timestamp"]

                records.append(record)
            except (ValueError, IndexError) as e:
                print(f"Skipping row due to error: {e}, Row: {row}")

    with open(output_file, 'wb') as out:
        fastavro.writer(out, schema, records)


def process_directory(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for csv_file in input_path.glob('*.csv'):
        output_file = output_path / "{0}.avro".format(csv_file.stem)
        print("Converting {0} to {1}".format(csv_file, output_file))
        convert_csv_to_avro(str(csv_file), str(output_file))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CSV files to Avro format')
    parser.add_argument('input_dir', help='Directory containing CSV files')
    parser.add_argument('output_dir', help='Directory for output Avro files')
    args = parser.parse_args()

    process_directory(args.input_dir, args.output_dir)