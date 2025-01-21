from flask import Flask, render_template, request, session, redirect, url_for
from opensky_api import OpenSkyApi
import time
import uuid
import requests
import json
import logging
import argparse
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import os
import pandas as pd
from threading import Thread
from queue import Queue
from google.cloud import storage
import plotly.graph_objects as go
import avro.schema
from avro.datafile import DataFileReader
from avro.io import DatumReader
from io import BytesIO
import threading

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'big_data'

# Add GCS configuration
class GCSConfig:
    BUCKET_NAME = "flights_data_merged"
    BLOB_PATH = "gs://flights_data_merged/flights_weekly_20241014_to_20241020.avro"

# Store histogram data globally
latest_arrival_times = []
MAX_DATA_POINTS = 1000  # Maximum number of arrival times to keep

class AirportData:
    def __init__(self, data_path: str) -> None:
        self._airports = pd.read_csv(data_path)

    def is_airport(self, icao: str) -> bool:
        return icao in self._airports['ident'].values

airport_data = AirportData("airports.csv")

class Config:
    SHOW_UI_ERRORS = False
    NIFI_ENDPOINT = "http://34.116.172.181:9091/contentListener"
    NIFI_GET_ENDPOINT = "http://34.116.172.181:8086"
    MAX_NULL_RESPONSES = 10

class GCSReader:
    def __init__(self, bucket_name: str, blob_path: str):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
        self.blob_path = blob_path
        
    def read_avro_from_gcs(self) -> List[Dict]:
        """Read Avro data from Google Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.blob_path)
            
            content = blob.download_as_bytes()
            bytes_io = BytesIO(content)
            
            reader = DataFileReader(bytes_io, DatumReader())
            data = [record for record in reader]
            reader.close()
            
            return data
            
        except Exception as e:
            logger.error(f"Error reading from GCS: {str(e)}")
            raise

def background_data_fetch(gcs_reader: GCSReader):
    """Background task to fetch Avro data every 10 seconds"""
    global latest_arrival_times
    
    while True:
        try:
            data = gcs_reader.read_avro_from_gcs()
            
            # Extract arrival times
            arrival_times = [
                record.get('flight_time_to_arrival', 0) 
                for record in data 
                if record.get('flight_time_to_arrival') is not None
            ]
            
            # Update global list
            latest_arrival_times = arrival_times[-MAX_DATA_POINTS:]
            
        except Exception as e:
            logger.error(f"Error in background fetch: {str(e)}")
            
        time.sleep(10)

def create_histogram() -> str:
    """Create a Plotly histogram of arrival times"""
    if not latest_arrival_times:
        return ""
        
    # Convert to minutes for better readability
    times_in_minutes = [time / 60 for time in latest_arrival_times]
    
    # Create histogram
    fig = go.Figure(data=[go.Histogram(
        x=times_in_minutes,
        nbinsx=20,
        name='Flight Times',
        marker_color='#4CAF50'
    )])
    
    # Update layout
    fig.update_layout(
        title='Distribution of Flight Times to Arrival',
        xaxis_title='Time to Arrival (minutes)',
        yaxis_title='Number of Flights',
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=400,
        margin=dict(t=50, b=50),
        bargap=0.1
    )
    
    return fig.to_html(include_plotlyjs=False, full_html=False)

def calculate_stats() -> Dict:
    """Calculate statistics from arrival times"""
    if not latest_arrival_times:
        return {}
        
    times_in_minutes = [time / 60 for time in latest_arrival_times]
    return {
        'total_flights': len(times_in_minutes),
        'avg_time': round(sum(times_in_minutes) / len(times_in_minutes), 1),
        'min_time': round(min(times_in_minutes), 1),
        'max_time': round(max(times_in_minutes), 1)
    }

# Keep existing classes and functions...
@dataclass
class FlightData:
    icao24: str
    timestamp: int
    host_id: str
    session_id: str
    lastSeen: int
    callSign: str
    arrivalAirport: str

# ... (keep all your existing error classes and helper functions)

@app.before_request
def before_request():
    try:
        if 'host_id' not in session:
            session['host_id'] = generate_host_id()
            logger.info(f"New session created with host ID: {session['host_id']}")
    except Exception as e:
        logger.error(f"Error in before_request: {str(e)}")

@app.route('/')
def index():
    return redirect(url_for('flight_data'))

@app.route('/flight-data', methods=['GET', 'POST'])
def flight_data():
    flight_list = []
    selected_flight = None
    session_id = None
    error_message = None
    time_to_arrival = None
    plot_html = ""
    stats_info = {}
    
    try:
        # Get flight data
        flight_list, flight_map, request_timestamp = get_flights_data()
        logger.debug(f"Retrieved {len(flight_list)} flights at timestamp {request_timestamp}")
        
        # Create histogram and calculate stats
        plot_html = create_histogram()
        stats_info = calculate_stats()
        
        if request.method == 'POST':
            selected_flight = request.form.get('flight')
            if selected_flight:
                logger.debug(f"Processing flight: {selected_flight}")
                
                if selected_flight in flight_map:
                    session_id = generate_session_id()
                    
                    # Send data to NiFi
                    success, error = send_flight_data_to_nifi(
                        flight_map[selected_flight],
                        session['host_id'],
                        session_id,
                        request_timestamp,
                        Config.NIFI_ENDPOINT
                    )
                    
                    if success:
                        # Start polling for arrival time
                        result_queue = Queue()
                        polling_thread = Thread(
                            target=poll_arrival_time,
                            args=(session_id, result_queue)
                        )
                        polling_thread.daemon = True
                        polling_thread.start()
                        
                        # Wait for result
                        result = result_queue.get(timeout=30)
                        if "error" in result:
                            error_message = result["error"]
                        else:
                            try:
                                time_value = float(result["time_to_arrival"])
                                time_in_minutes = abs(time_value) / 60
                                time_to_arrival = str(round(time_in_minutes))
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error formatting time value: {str(e)}")
                                error_message = "Error processing arrival time"
                    else:
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
                         time_to_arrival=time_to_arrival,
                         host_id=session.get('host_id'),
                         session_id=session_id,
                         error_message=error_message if Config.SHOW_UI_ERRORS else None,
                         show_errors=Config.SHOW_UI_ERRORS,
                         plot_html=plot_html,
                         stats_info=stats_info)

def main():
    # Initialize GCS reader
    gcs_reader = GCSReader(GCSConfig.BUCKET_NAME, GCSConfig.BLOB_PATH)
    
    # Start background fetch thread
    fetch_thread = threading.Thread(target=background_data_fetch, args=(gcs_reader,))
    fetch_thread.daemon = True
    fetch_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()