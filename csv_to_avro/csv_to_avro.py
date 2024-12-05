import fastavro
import csv
import os
import argparse
from pathlib import Path

schema = {
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

def convert_csv_to_avro(input_file, output_file):
    records = []
    with open(input_file, 'r', encoding='latin-1') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            try:
                record = {
                    "latitude": float(row[0]),
                    "longitude": float(row[1]),
                    "arrival_airport": row[2],
                    "arrival_airport_latitude": float(row[3]),
                    "arrival_airport_longitude": float(row[4]),
                    "time": int(float(row[5])),
                    "horizontal_velocity": float(row[6]),
                    "altitude": float(row[7]),
                    "vertical_velocity": float(row[8]),
                    "heading": float(row[9]),
                    "distance_to_destination": float(row[10]),
                    "arrival_time": int(float(row[11])),
                    "time_to_arrival": int(float(row[12])),
                    "temperature": float(row[13]),
                    "feels_like": float(row[14]),
                    "condition": row[15],
                    "wind_speed": float(row[16]),
                    "humidity": float(row[17]),
                    "precipitation": float(row[18]),
                    "visibility": float(row[19]),
                    "pressure": float(row[20]),
                    "uv_index": float(row[21])
                }
                records.append(record)
            except ValueError as e:
                print("Skipping row due to invalid value: %s, Row: %s" % (e, row))



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