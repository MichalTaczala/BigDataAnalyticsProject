import torch
import os
import logging

import config
from model.scaler import Scaler
from model.model import FlightNN
from flight_data.models import FlightInfo
from flight_data.airports_data import AirportData
from data_collection.models import CombinedDatapoint
from flight_data.flight_data import FlightData
from data_collection.flight_collector import FlightCollector
import numpy as np
from gcp.load_file import GCSLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def inference(X: np.ndarray) -> np.ndarray:
    logging.info("Starting inference")
    loader = GCSLoader(bucket_name="models-big-data-mini")
    best_model = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best_model.pth")
    if not os.path.isfile(best_model):
        loader.load_to_path("best_model.pth", best_model)
    logging.info("Weights")
    model = FlightNN(input_size=2)
    model.load(best_model)

    logging.info("Model loaded")

    scaler_x_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scaler_X.json")
    if not os.path.isfile(scaler_x_path):
        loader.load_to_path("scaler_X.json", scaler_x_path)
    scaler_x = Scaler.load(scaler_x_path)

    logging.info("Scaler X loaded")

    scaler_y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scaler_y.json")
    if not os.path.isfile(scaler_y):
        loader.load_to_path("scaler_y.json", scaler_y)
    scaler_y = Scaler.load(scaler_y)

    logging.info("Scaler Y loaded")

    assert X.shape[1] == 2, f"Expected 2 features, got {X.shape[1]}"

    X_scaled = scaler_x.transform(X)
    X_tensor = torch.FloatTensor(X_scaled).reshape(-1, 2)

    logging.info("Data transformed %s", X_tensor)
    y_pred = model(X_tensor)
    logging.info("Prediction made %s", y_pred.detach().numpy())
    return scaler_y.inverse_transform(y_pred.detach().numpy().reshape(-1, 1)).ravel()


def get_data(flights: list[FlightInfo]) -> list[CombinedDatapoint]:
    airports = AirportData(config.AIRPORTS_DATA)
    flight_data = FlightData(airports)
    collector = FlightCollector(flight_data)

    data: list[CombinedDatapoint] = []
    for flight in flights:
        datapoints = collector.flight_data.get_flight_datapoints(flight, ignore_min_distance=True)
        if not datapoints:
            raise ValueError(f"Missing datapoints for flight {flight.icao24}")

        combined_datapoints = collector.get_weather_data_for_flight_datapoints(datapoints)
        data.append(combined_datapoints[-1])

    return data


def get_features(data: list[CombinedDatapoint]) -> np.ndarray:
    return np.array([[datapoint.flight.distance_to_destination, datapoint.flight.horizontal_speed] for datapoint in data])


if __name__ == "__main__":
    # Inference
    X = np.array([[1200, 500]])
    y_pred = inference(X)
    print(f"Predicted delay: {y_pred:.2f} seconds")
