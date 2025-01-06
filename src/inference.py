import torch
import os

from PIL.ImageOps import scale

from model.scaler import Scaler
from model.model import FlightNN
import numpy as np
from gcp.load_file import GCSLoader


def inference(X: np.ndarray) -> float:
    loader = GCSLoader(bucket_name="models-big-data-mini")
    best_model = "best_model.pth"
    if not os.path.isfile(best_model):
        loader.load_to_path("best_model.pth", best_model)

    model = FlightNN(input_size=2)
    model.load(best_model)

    scaler_x_path = "scaler_X.json"
    if not os.path.isfile(scaler_x_path):
        loader.load_to_path("scaler_X.json", scaler_x_path)
    scaler_x = Scaler.load(scaler_x_path)

    scaler_y = "scaler_y.json"
    if not os.path.isfile(scaler_y):
        loader.load_to_path("scaler_y.json", scaler_y)
    scaler_y = Scaler.load(scaler_y)

    assert X.shape[1] == 2, f"Expected 2 features, got {X.shape[1]}"

    X_scaled = scaler_x.transform(X)
    X_tensor = torch.FloatTensor(X_scaled).reshape(1, -1)
    y_pred = model(X_tensor)
    return scaler_y.inverse_transform(y_pred.detach().numpy().reshape(-1, 1)).ravel()[0]


if __name__ == "__main__":
    # Inference
    X = np.array([[1200, 500]])
    y_pred = inference(X)
    print(f"Predicted delay: {y_pred:.2f} seconds")
