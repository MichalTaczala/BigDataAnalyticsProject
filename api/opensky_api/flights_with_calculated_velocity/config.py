import yaml

with open('credentials.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

START_TIME=1730890584
END_TIME=1730896984
NAME_OF_OUTPUT_FILE="example.csv"
LIMIT=120
WEATHER_API_KEY=config["weather_api"]
BASE_URL='http://api.weatherapi.com/v1/history.json'
