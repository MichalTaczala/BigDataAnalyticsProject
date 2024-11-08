from opensky_api import OpenSkyApi
from config import START_TIME, END_TIME, NAME_OF_OUTPUT_FILE, LIMIT
from get_flights import extract_six_char_string_values, save_flight_data_to_csv

api = OpenSkyApi()

data = api.get_flights_from_interval(START_TIME, END_TIME)

icao24 = []
print(data)
print(len(data))

for flight in data[:LIMIT]:
    icao24_temp = extract_six_char_string_values(flight)
    
    flight_data = api.get_track_by_aircraft(icao24_temp[0], START_TIME)
    #print(icao24_temp[0])
    print(flight_data)
    if flight_data is not None:
        save_flight_data_to_csv(flight_data, NAME_OF_OUTPUT_FILE)
    else:
        flight_data = api.get_track_by_aircraft(icao24_temp[0], END_TIME)
        print(flight_data)
        if flight_data is not None:
            save_flight_data_to_csv(flight_data, NAME_OF_OUTPUT_FILE)
            print(flight_data)
    
