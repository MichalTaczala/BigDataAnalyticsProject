import torch

from model.scaler import Scaler
from model.model import FlightNN
import numpy as np
from gcp.load_file import GCSLoader


def inference(scaler_x: Scaler, scaler_y: Scaler, model: FlightNN, X: np.ndarray) -> float:
    assert X.shape[1] == 2, f"Expected 2 features, got {X.shape[1]}"

    X_scaled = scaler_x.transform(X)
    X_tensor = torch.FloatTensor(X_scaled).reshape(1, -1)
    y_pred = model(X_tensor)
    return scaler_y.inverse_transform(y_pred.detach().numpy().reshape(-1, 1)).ravel()[0]


if __name__ == "__main__":
    # Load model and scalers
    loader = GCSLoader(bucket_name="models-big-data-mini")

    model = FlightNN(input_size=2)
    model.load(loader.load_to_memory("best_model.pth"))

    scaler_x = Scaler.load(loader.load_to_temp("scaler_X.json"))
    scaler_y = Scaler.load(loader.load_to_temp("scaler_y.json"))

    # Inference
    X = np.array([[1200, 500]])
    y_pred = inference(scaler_x, scaler_y, model, X)
    print(f"Predicted delay: {y_pred:.2f} seconds")
