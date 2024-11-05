import csv
from opensky_api import OpenSkyApi
from config import START_TIME, END_TIME, NAME_OF_OUTPUT_FILE
from velocity import calculate_average_velocity, calculate_total_distance_and_time

def extract_six_char_string_values(flight_data):
    data_dict = vars(flight_data)
    
    return [value for value in data_dict.values() if isinstance(value, str) and len(value) == 6]


def save_flight_data_to_csv(flight_data, filename, write_header=False):
    data_dict = vars(flight_data)
    total_distance, total_time = calculate_total_distance_and_time(data_dict['path'])
    average_velocity = calculate_average_velocity(total_distance, total_time)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        if write_header:
            writer.writerow(['callsign', 'endtime', 'icao24', 'starttime', 'total_distance (km)', 'total_time (s)', 'average_velocity (km/h)'])

        # Write a single row for the flight with the average velocity
        writer.writerow([
            data_dict['callsign'], data_dict['endTime'], data_dict['icao24'], 
            data_dict['startTime'], total_distance, total_time, average_velocity
        ])

api = OpenSkyApi()


# Call the get_flights_from_interval function
data = api.get_flights_from_interval(START_TIME, END_TIME)

icao24 = []
print(data)
print(len(data))

for flight in data[:15]:
    icao24_temp = extract_six_char_string_values(flight)
    
    flight_data = api.get_track_by_aircraft(icao24_temp, START_TIME)
    if flight_data is not None:
        save_flight_data_to_csv(flight_data, NAME_OF_OUTPUT_FILE)
    print(icao24_temp)
    print(flight_data)
    