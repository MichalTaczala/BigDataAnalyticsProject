from opensky_api import OpenSkyApi
import csv
from datetime import datetime, timezone

def save_aircraft_state_vectors(icao24, time, input_file):
    """
    Retrieve and save the current state vectors for the specified aircraft to a CSV file.
    
    Args:
    icao24 (str): The ICAO24 address of the aircraft.
    
    Returns:
    None
    """
    # Initialize the OpenSky API
    api = OpenSkyApi()

    # Retrieve the current state vectors for the specified aircraft
    states = api.get_states(icao24=icao24, time_secs=time)
    
    # Check if any state vectors were retrieved
    if states and states.states:
        # Open the CSV file for writing
        with open(input_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write the header
            writer.writerow([
                'icao24', 'callsign', 'origin_country', 'time_position', 'last_contact',
                'longitude', 'latitude', 'baro_altitude', 'on_ground', 'velocity',
                'true_track', 'vertical_rate', 'geo_altitude', 'squawk', 'spi', 'position_source'
            ])
            
            # Write the data
            for state in states.states:
                writer.writerow([
                    state.icao24,
                    state.callsign,
                    state.origin_country,
                    state.time_position,
                    state.last_contact,
                    state.longitude,
                    state.latitude,
                    state.baro_altitude,
                    state.on_ground,
                    state.velocity,
                    state.true_track,
                    state.vertical_rate,
                    state.geo_altitude,
                    state.squawk,
                    state.spi,
                    state.position_source
                ])
        
        print("Aircraft state vectors saved successfully.")
    else:
        print("No state vectors found for the specified aircraft.")

# # Example usage
# icao24 = 'a403ca'  # Example ICAO24 address
# input_file="flights_vectors12.csv"
# save_aircraft_state_vectors(icao24, 0, input_file)