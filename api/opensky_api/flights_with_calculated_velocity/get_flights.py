import csv
from opensky_api import OpenSkyApi
from config import START_TIME, END_TIME, NAME_OF_OUTPUT_FILE
from velocity import calculate_average_velocity, calculate_total_distance_and_time
from weather import get_weather_data, find_weather_data_by_unixtime
import time
from datetime import datetime, timedelta
import os

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

def save_flight_data_to_csv(flight_data, filename, write_header=True):
    data_dict = vars(flight_data)
    
    #Calculate data every 20 rows in track, as intervals are 10-60 seconds
    for i in range(0, len(data_dict['path']), 20):
        temp1 = data_dict['path']
        temp = temp1[i:i+20]
        print("#####")
        print(temp)
        total_distance, total_time = calculate_total_distance_and_time(temp)
        average_velocity = calculate_average_velocity(total_distance, total_time)

        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)

            if not file_exists and write_header:
                writer.writerow(['callsign', 'endtime', 'icao24', 'starttime', 'total_distance(km)', 'total_time(s)', 'average_velocity(m/s)',
                             'latitude', 'longitude','Temperature(°C)', 'Feels Like(°C)', 
                             'Condition', 'Wind Speed(kph)', 'Humidity(%)', 'Precipitation(mm)', 
                             'Visibility(km)', 'Pressure(mb)', 'UV Index' ])
            #TODO Create better wrapper function
            #Add Weather data
            lat = temp[0][1]
            lon = temp[0][2]
            start_time_unix=temp[0][0]

            start_time_unix1 = round_unixtime_to_nearest_minute(start_time_unix)
            start_time= transform_unix_timestamp(start_time_unix1)
            
            total_weather_data = get_weather_data(lat, lon, start_time)
            weather = find_weather_data_by_unixtime(total_weather_data, start_time_unix1)
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
            writer.writerow([
            data_dict['callsign'], temp[-1][0], data_dict['icao24'], 
            start_time_unix1, total_distance, total_time, average_velocity, lat, lon, 
            weather['Temperature (°C)'], weather['Feels Like (°C)'], weather['Condition'], 
            weather['Wind Speed (kph)'], weather['Humidity (%)'], weather['Precipitation (mm)'],
            weather['Visibility (km)'], weather['Pressure (mb)'], weather['UV Index']
            ])    