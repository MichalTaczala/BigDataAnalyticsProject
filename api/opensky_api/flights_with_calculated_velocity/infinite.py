from opensky_api import OpenSkyApi
from get_flights import extract_six_char_string_values, save_flight_data_to_csv
from datetime import datetime, timedelta
from airports_data import AirportData
from flight_data import FlightData
import time

airports = AirportData("api/opensky_api/flights_with_calculated_velocity/airports.csv")
flight_data = FlightData(airports)

# Start from X days ago
days_offset = 22
hours_offset = 0

# Loop to cover 2-hour sliding windows from 29 days ago up to the current time
while days_offset >= 0:
    # Calculate start and end time for the 2-hour window
    current_time = datetime.now()
    end_time = current_time - timedelta(days=days_offset, hours=hours_offset)
    start_time = end_time - timedelta(hours=2)

    # Convert to UNIX timestamps
    START_TIME = int(start_time.timestamp())
    END_TIME = int(end_time.timestamp())

    # Generate a dynamic output file name
    start_date_str = start_time.strftime('%Y%m%d_%H%M')
    end_date_str = end_time.strftime('%Y%m%d_%H%M')
    NAME_OF_OUTPUT_FILE = f"flights_{start_date_str}_to_{end_date_str}.csv"

    print(f"Processing data from {start_time} to {end_time}...")

    # Fetch data from OpenSky API
    data = flight_data.get_flights(START_TIME, END_TIME)
    if data is None:
        print("No data returned. Retrying...")

    print(data)
    print(len(data))

    for flight in data:
        datapoints = flight_data.get_flight_datapoints(flight)
        if not datapoints:
            print("No data returned. Skipping...")
            continue
        print(len(datapoints))
        save_flight_data_to_csv(datapoints, NAME_OF_OUTPUT_FILE)

    # Adjust for the next 2-hour window
    hours_offset += 2
    if hours_offset >= 24:
        hours_offset -= 24
        days_offset -= 1

    # Optional: Add a short sleep to avoid rapid iteration (e.g., 1 second)
    time.sleep(1)
