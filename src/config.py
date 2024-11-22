import os
import yaml

AIRPORTS_DATA = os.path.join("data", "static", "airports.csv")
DOWNLOAD_DATA_DIR = os.path.join("data", "downloaded_data")
WEATHER_API_URL = "http://api.weatherapi.com/v1/history.json"

with open('credentials.yaml') as file:
    _config = yaml.load(file, Loader=yaml.FullLoader)
OPENSKY_USERNAME = _config["open_sky"]['username']
OPENSKY_PASSWORD = _config["open_sky"]['password']
WEATHER_API_KEY = _config["weather_api"]
