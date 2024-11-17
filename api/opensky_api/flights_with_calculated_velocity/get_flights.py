import csv
from opensky_api import OpenSkyApi
from config import START_TIME, END_TIME, NAME_OF_OUTPUT_FILE
from velocity import calculate_average_velocity, calculate_total_distance_and_time
from weather import get_weather_data, find_weather_data_by_unixtime
import time
from datetime import datetime, timedelta
import os
from flight_data import FlightDatapoint

def extract_six_char_string_values(flight_data):
    data_dict = vars(flight_data)
    
    return [value for value in data_dict.values() if isinstance(value, str) and len(value.strip()) == 6]

def round_unixtime_to_nearest_minute(unix_timestamp):
    # Convert the Unix timestamp to a datetime object
    dt_object = datetime.fromtimestamp(unix_timestamp)
    # Calculate the number of seconds since the start of the minute
    seconds = dt_object.second + dt_object.microsecond / 1e6
    # If the number of seconds is 30 or more, round up to the next minute
    if seconds >= 30:
        dt_object = dt_object + timedelta(minutes=1)
    # Set the seconds and microseconds to 0 to round to the nearest minute
    dt_object = dt_object.replace(second=0, microsecond=0)
    # Convert the rounded datetime object back to a Unix timestamp
    rounded_timestamp = int(time.mktime(dt_object.timetuple()))
    return rounded_timestamp

def transform_unix_timestamp(unix_timestamp):
    # Convert the Unix timestamp to a datetime object
    dt_object = datetime.fromtimestamp(unix_timestamp)
    # Format the datetime object to the desired string format
    formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')
    return formatted_date

def save_flight_data_to_csv(flight_data: list[FlightDatapoint], filename, write_header=True):
    for datapoint in flight_data:
        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            time_to_minute = round_unixtime_to_nearest_minute(datapoint.time)

            if not file_exists and write_header:
                writer.writerow(datapoint.get_names() + ['Temperature(°C)', 'Feels Like(°C)',
                             'Condition', 'Wind Speed(kph)', 'Humidity(%)', 'Precipitation(mm)', 
                             'Visibility(km)', 'Pressure(mb)', 'UV Index' ])
            
            total_weather_data = get_weather_data(datapoint.latitude, datapoint.longitude, transform_unix_timestamp(time_to_minute))
            if total_weather_data is None:
                weather = {
                    'Temperature (°C)': 'NA',
                    'Feels Like (°C)': 'NA',
                    'Condition': 'NA',
                    'Wind Speed (kph)': 'NA',
                    'Humidity (%)': 'NA',
                    'Precipitation (mm)': 'NA',
                    'Visibility (km)': 'NA',
                    'Pressure (mb)': 'NA',
                    'UV Index': 'NA'
                }
            else:
                weather = find_weather_data_by_unixtime(total_weather_data, time_to_minute)
                #print(weather)
                if weather is None:
                    weather = {
                        'Temperature (°C)': 'NA',
                        'Feels Like (°C)': 'NA',
                        'Condition': 'NA',
                        'Wind Speed (kph)': 'NA',
                        'Humidity (%)': 'NA',
                        'Precipitation (mm)': 'NA',
                        'Visibility (km)': 'NA',
                        'Pressure (mb)': 'NA',
                        'UV Index': 'NA'
                    }

            #Writing data
            writer.writerow(datapoint.get_values() + [
            weather['Temperature (°C)'], weather['Feels Like (°C)'], weather['Condition'], 
            weather['Wind Speed (kph)'], weather['Humidity (%)'], weather['Precipitation (mm)'],
            weather['Visibility (km)'], weather['Pressure (mb)'], weather['UV Index']
            ])    