from opensky_api import OpenSkyApi
from get_flights import extract_six_char_string_values, save_flight_data_to_csv
from datetime import datetime, timedelta
import time

api = OpenSkyApi(username= 'fifi', password= 'UtqpsWju8@sbVN7')

# Start from X days ago
days_offset = 28
hours_offset = 0

# Loop to cover 2-hour sliding windows from 29 days ago up to the current time
while days_offset >= 0:
    try:
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
        data = api.get_flights_from_interval(START_TIME, END_TIME)

        if data is None:
            print("No data returned. Retrying...")

        print(data)
        print(len(data))

        for flight in data:
            icao24_temp = extract_six_char_string_values(flight)
            if icao24_temp:
                flight_data = api.get_track_by_aircraft(icao24_temp[0], START_TIME)
                print(flight_data)
                if flight_data is not None:
                    save_flight_data_to_csv(flight_data, NAME_OF_OUTPUT_FILE)
                else:
                    flight_data = api.get_track_by_aircraft(icao24_temp[0], END_TIME)
                    print(flight_data)
                    if flight_data is not None:
                        save_flight_data_to_csv(flight_data, NAME_OF_OUTPUT_FILE)
                        print(flight_data)

        # Adjust for the next 2-hour window
        hours_offset += 2
        if hours_offset >= 24:
            hours_offset -= 24
            days_offset -= 1

        # Optional: Add a short sleep to avoid rapid iteration (e.g., 1 second)
        time.sleep(1)

    except Exception as e:
        # Catch any exception, print it, wait for 16 minutes, and retry
        print(f"An error occurred: {e}")
        print("Waiting for 16 minutes before retrying...")
        time.sleep(960)  # 960 seconds = 16 minutes
