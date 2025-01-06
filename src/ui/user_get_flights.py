from flask import Flask, render_template, request
from opensky_api import OpenSkyApi
import time
import random

app = Flask(__name__)

def get_flight_data():
    api = OpenSkyApi()
    current_time = int(time.time())
    two_hours_ago = current_time - 7200
    
    data = api.get_flights_from_interval(two_hours_ago, current_time)
    flights = []
    for flight in data:
        if flight.callsign:  
            flights.append({
                'icao24': flight.icao24,
                'callsign': flight.callsign.strip()  
            })
    return flights

def get_random_delay():
    return round(random.uniform(0, 120), 1)

@app.route('/', methods=['GET', 'POST'])
def index():
    flight_list = get_flight_data()
    selected_flight = None
    delay = None
    selected_icao = None
    
    if request.method == 'POST':
        selected_callsign = request.form.get('flight')
        if selected_callsign:
            # Find the corresponding ICAO for the selected callsign
            for flight in flight_list:
                if flight['callsign'] == selected_callsign:
                    selected_flight = selected_callsign
                    selected_icao = flight['icao24']
                    delay = get_random_delay()
                    break
    
    return render_template('index.html', 
                         flights=flight_list,
                         selected_flight=selected_flight,
                         selected_icao=selected_icao,
                         delay=delay)

if __name__ == '__main__':
    app.run(debug=True)