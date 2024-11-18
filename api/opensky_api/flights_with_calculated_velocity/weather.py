import requests
import time
from datetime import datetime, timedelta
import csv
from config import WEATHER_API_KEY, BASE_URL

def interpolate_minute_data(hourly_data):
    minute_data = []
    for i in range(len(hourly_data) - 1):
        start_hour = hourly_data[i]
        end_hour = hourly_data[i + 1]

        start_time = datetime.strptime(start_hour['time'], '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_hour['time'], '%Y-%m-%d %H:%M')
        delta_minutes = (end_time - start_time).seconds // 60

        for minute_offset in range(delta_minutes):
            interpolated_time = start_time + timedelta(minutes=minute_offset)
            temp_c = start_hour['temp_c'] + (minute_offset / delta_minutes) * (end_hour['temp_c'] - start_hour['temp_c'])
            wind_kph = start_hour['wind_kph'] + (minute_offset / delta_minutes) * (end_hour['wind_kph'] - start_hour['wind_kph'])
            humidity = start_hour['humidity'] + (minute_offset / delta_minutes) * (end_hour['humidity'] - start_hour['humidity'])
            precip_mm = start_hour['precip_mm'] + (minute_offset / delta_minutes) * (end_hour['precip_mm'] - start_hour['precip_mm'])
            visibility_km = start_hour['vis_km'] + (minute_offset / delta_minutes) * (end_hour['vis_km'] - start_hour['vis_km'])
            pressure_mb = start_hour['pressure_mb'] + (minute_offset / delta_minutes) * (end_hour['pressure_mb'] - start_hour['pressure_mb'])
            feelslike_c = start_hour['feelslike_c'] + (minute_offset / delta_minutes) * (end_hour['feelslike_c'] - start_hour['feelslike_c'])
            uv_index = start_hour['uv'] + (minute_offset / delta_minutes) * (end_hour['uv'] - start_hour['uv'])
            condition = start_hour['condition']['text']  # Assuming condition stays the same for simplicity

            minute_data.append({
                'time': interpolated_time.strftime('%Y-%m-%d %H:%M'),
                'temp_c': round(temp_c, 2),
                'wind_kph': round(wind_kph, 2),
                'humidity': round(humidity, 2),
                'precip_mm': round(precip_mm, 2),
                'visibility_km': round(visibility_km, 2),
                'pressure_mb': round(pressure_mb, 2),
                'feelslike_c': round(feelslike_c, 2),
                'uv_index': round(uv_index, 2),
                'condition': condition
            })
    return minute_data

def get_weather_data(latitude, longitude, date):
    location_query = "{},{}".format(latitude, longitude)
    print(location_query, date)
    params = {
        'key': WEATHER_API_KEY,
        'q': location_query,
        'dt': date
    }

    # Make the request
    response = requests.get(BASE_URL, params=params)
    
    # Check the response
    if response.status_code == 200:
        weather_data = response.json()
        if 'forecast' in weather_data and 'forecastday' in weather_data['forecast']:
            hourly_data = weather_data['forecast']['forecastday'][0]['hour']
            #print(hourly_data)
            minute_data = interpolate_minute_data(hourly_data)

            # Store minute-by-minute data in a list
            weather_data_list = []
            for minute_entry in minute_data:
                # Convert time to Unix timestamp
                unix_time = int(time.mktime(datetime.strptime(minute_entry['time'], '%Y-%m-%d %H:%M').timetuple()))

                weather_data_list.append({
                    'UnixTime': unix_time,
                    'Temperature (°C)': minute_entry['temp_c'],
                    'Feels Like (°C)': minute_entry['feelslike_c'],
                    'Condition': minute_entry['condition'],
                    'Wind Speed (kph)': minute_entry['wind_kph'],
                    'Humidity (%)': minute_entry['humidity'],
                    'Precipitation (mm)': minute_entry['precip_mm'],
                    'Visibility (km)': minute_entry['visibility_km'],
                    'Pressure (mb)': minute_entry['pressure_mb'],
                    'UV Index': minute_entry['uv_index']
                })

            
            print("Weather data stored in an object")
            return weather_data_list
        else:
            print("No forecast data found.")
            return None
    else:
        print(response.status_code)
        print(response.raw)
        print("Failed to retrieve data not 200")
        return None

def find_weather_data_by_unixtime(weather_data_list, unix_time):
    for row in weather_data_list:
        if row['UnixTime'] == unix_time:
            return row

    return None

