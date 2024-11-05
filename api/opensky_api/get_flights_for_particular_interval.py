import json
from opensky_api import OpenSkyApi
from get_states import save_aircraft_state_vectors


def extract_six_char_string_values(flight_data):
    # Use vars() to get the dictionary of the object's attributes
    data_dict = vars(flight_data)
    
    # Filter the dictionary to get only string values of length 6
    return [value for value in data_dict.values() if isinstance(value, str) and len(value) == 6]


# Instantiate the API client
api = OpenSkyApi()


# Call the get_flights_from_interval function
data = api.get_flights_from_interval(1633072800, 1633073960)

icao24 = []
print("elo")
for flight in data:
    icao24_temp = extract_six_char_string_values(flight)
    print(icao24_temp)
    save_aircraft_state_vectors(icao24_temp, 1633072800, "new_flights_vectors111111.csv")


