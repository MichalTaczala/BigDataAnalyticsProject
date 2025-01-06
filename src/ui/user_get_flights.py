from flask import Flask, render_template, request, session
from opensky_api import OpenSkyApi
import time
import random
import uuid
import requests
import json
import logging
import argparse
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
#app.secret_key = 'your-secret-key-here'  

class Config:
    SHOW_UI_ERRORS = False
    NIFI_ENDPOINT = "https://nifiexample?"

@dataclass
class FlightData:
    icao24: str
    firstSeen: int
    estDepartureAirport: Optional[str]
    lastSeen: int
    estArrivalAirport: Optional[str]
    callsign: Optional[str]
    estDepartureAirportHorizDistance: Optional[int]
    estDepartureAirportVertDistance: Optional[int]
    estArrivalAirportHorizDistance: Optional[int]
    estArrivalAirportVertDistance: Optional[int]
    departureAirportCandidatesCount: Optional[int]
    arrivalAirportCandidatesCount: Optional[int]
    host_id: str
    request_id: str

class FlightTrackerError(Exception):
    pass

class NiFiConnectionError(FlightTrackerError):
    pass

class FlightDataError(FlightTrackerError):
    pass

def generate_host_id() -> str:
    try:
        return str(uuid.uuid4())
    except Exception as e:
        logger.error(f"Error generating host ID: {str(e)}")
        raise FlightTrackerError("Failed to generate host ID")

def generate_request_id() -> str:
    """Generate a unique request ID for each flight check"""
    try:
        return str(uuid.uuid4())
    except Exception as e:
        logger.error(f"Error generating request ID: {str(e)}")
        raise FlightTrackerError("Failed to generate request ID")

def get_flights_data() -> Tuple[List[str], Dict[str, object]]:
    """
    Get flight data from OpenSky API 
    """
    try:
        api = OpenSkyApi()
        current_time = int(time.time())
        two_hours_ago = current_time - 7200
        
        logger.debug(f"Fetching flights from {two_hours_ago} to {current_time}")
        flights = api.get_flights_from_interval(two_hours_ago, current_time)
        
        if not flights:
            logger.warning("No flight data received from OpenSky API")
            return [], {}
            
        # Create a mapping of flight IDs to full flight objects
        flight_map = {flight.icao24: flight for flight in flights}
        flight_ids = list(flight_map.keys())
        
        return flight_ids, flight_map
    except Exception as e:
        logger.error(f"Error fetching flight data: {str(e)}")
        raise FlightDataError("Failed to fetch flight data from OpenSky API")

def get_random_delay() -> float:
    return round(random.uniform(0, 120), 1)

def send_flight_data_to_nifi(flight, host_id: str, request_id: str, nifi_endpoint: str) -> Tuple[bool, Optional[str]]:
    """
    Send flight data to NiFi endpoint with host and request IDs
    
    Returns:
        Tuple[bool, Optional[str]]: (success status, error message if any)
    """
    try:
        logger.info(f"Preparing flight data for NiFi - Flight: {flight.icao24}, Host ID: {host_id}, Request ID: {request_id}")
        
        flight_data = FlightData(
            icao24=flight.icao24,
            firstSeen=flight.firstSeen,
            estDepartureAirport=flight.estDepartureAirport,
            lastSeen=flight.lastSeen,
            estArrivalAirport=flight.estArrivalAirport,
            callsign=flight.callsign,
            estDepartureAirportHorizDistance=flight.estDepartureAirportHorizDistance,
            estDepartureAirportVertDistance=flight.estDepartureAirportVertDistance,
            estArrivalAirportHorizDistance=flight.estArrivalAirportHorizDistance,
            estArrivalAirportVertDistance=flight.estArrivalAirportVertDistance,
            departureAirportCandidatesCount=flight.departureAirportCandidatesCount,
            arrivalAirportCandidatesCount=flight.arrivalAirportCandidatesCount,
            host_id=host_id,
            request_id=request_id
        )

        flight_dict = {k: v for k, v in flight_data.__dict__.items() if v is not None}
        
        headers = {
            'Content-Type': 'application/json',
            'X-Host-ID': host_id,
            'X-Request-ID': request_id
        }
        
        logger.debug(f"Sending request to NiFi endpoint: {nifi_endpoint}")
        logger.debug(f"Request payload: {json.dumps(flight_dict, indent=2)}")
        
        response = requests.post(
            nifi_endpoint,
            data=json.dumps(flight_dict),
            headers=headers
        )
        
        response.raise_for_status()
        logger.info(f"Successfully sent flight data to NiFi - Request ID: {request_id}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error sending data to NiFi: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error while sending data to NiFi: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

@app.before_request
def before_request():
    try:
        if 'host_id' not in session:
            session['host_id'] = generate_host_id()
            logger.info(f"New session created with host ID: {session['host_id']}")
    except Exception as e:
        logger.error(f"Error in before_request: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    flight_list = []
    selected_flight = None
    delay = None
    request_id = None
    error_message = None
    
    try:
        flight_list, flight_map = get_flights_data()
        logger.debug(f"Retrieved {len(flight_list)} flights")
        
        if request.method == 'POST':
            selected_flight = request.form.get('flight')
            if selected_flight:
                logger.debug(f"Processing flight: {selected_flight}")
                
                if selected_flight in flight_map:
                    delay = get_random_delay()
                    request_id = generate_request_id()
                    
                    nifi_endpoint = Config.NIFI_ENDPOINT
                    success, error = send_flight_data_to_nifi(
                        flight_map[selected_flight],
                        session['host_id'],
                        request_id,
                        nifi_endpoint
                    )
                    if not success:
                        error_message = error
                else:
                    logger.warning(f"Selected flight {selected_flight} not found in current data")
                    error_message = "Selected flight not found in current data"
    
    except FlightTrackerError as e:
        error_message = str(e)
        logger.error(f"FlightTrackerError: {str(e)}")
    except Exception as e:
        error_message = "An unexpected error occurred"
        logger.error(f"Unexpected error in index route: {str(e)}")
    
    return render_template('index.html', 
                         flights=flight_list,
                         selected_flight=selected_flight,
                         delay=delay,
                         host_id=session.get('host_id'),
                         request_id=request_id,
                         error_message=error_message if Config.SHOW_UI_ERRORS else None,
                         show_errors=Config.SHOW_UI_ERRORS)

def main():
    parser = argparse.ArgumentParser(description='Flight Tracker Application')
    parser.add_argument('--show-errors', action='store_true', 
                      help='Enable error messages in the UI')
    parser.add_argument('--port', type=int, default=5000,
                      help='Port to run the application on')
    parser.add_argument('--host', default='127.0.0.1',
                      help='Host to run the application on')
    parser.add_argument('--debug', action='store_true',
                      help='Run in debug mode')
    
    args = parser.parse_args()
    
    Config.SHOW_UI_ERRORS = args.show_errors
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()