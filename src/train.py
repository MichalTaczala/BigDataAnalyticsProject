from gcp.load_file import GCSLoader
import os
import tempfile
import glob
import numpy as np
import avro.datafile
import avro.io
from schema import SCHEMA
from sklearn.model_selection import train_test_split
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from model.model import FlightNN
from model.scaler import Scaler


def load_avro_data(schema_dict, data_path):
    # Get list of numeric fields (excluding strings and target variable)
    numeric_fields = [
        field["name"] for field in schema_dict["fields"]
        if field["type"] in ["double", "long"]
        and field["name"] != "flight_time_to_arrival"
    ]

    # Initialize lists to store features and target
    features = []
    targets = []

    # Process each AVRO file in the directory
    for avro_file in glob.glob(data_path):
        with avro.datafile.DataFileReader(open(avro_file, 'rb'), avro.io.DatumReader()) as reader:
            for record in reader:
                # Extract numeric features
                feature_row = [record[field] for field in numeric_fields]
                features.append(feature_row)

                # Extract target variable
                targets.append(record["flight_time_to_arrival"])

    # Convert to numpy arrays
    X = np.array(features)
    y = np.array(targets)

    # Get feature names for reference
    feature_names = numeric_fields

    return X, y, feature_names


# Create PyTorch Dataset
class FlightDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


# Training function
def train_model(model, train_loader, val_loader, criterion, optimizer, epochs, device):
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)
        train_losses.append(train_loss)

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                y_pred = model(X_batch)
                val_loss += criterion(y_pred, y_batch).item()

        val_loss /= len(val_loader)
        val_losses.append(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'best_model.pth')

        if epoch % 5 == 0:
            print(f'Epoch {epoch}: Train Loss = {train_loss:.4f}, Val Loss = {val_loss:.4f}')


if __name__ == "__main__":
    gcs = GCSLoader("raw_avros")
    with tempfile.TemporaryDirectory() as folder:
        for blob_name in gcs.list_files():
            gcs.load_to_path(blob_name, os.path.join(folder, blob_name))

        X, y, feature_names = load_avro_data(SCHEMA, os.path.join(folder, "*.avro"))

    X_important = X[:, [10, 6]]

    # Scale features and target
    scaler_X = Scaler()
    scaler_y = Scaler()

    X_scaled = scaler_X.fit_transform(X_important)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    scaler_X.save('scaler_X.json')
    scaler_y.save('scaler_y.json')

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.1, random_state=42)

    # Set up training parameters
    BATCH_SIZE = 1024
    EPOCHS = 2
    LEARNING_RATE = 0.001
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Create datasets and dataloaders
    train_dataset = FlightDataset(X_train, y_train)
    test_dataset = FlightDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

    # Initialize model and training components
    model = FlightNN(input_size=X_important.shape[1]).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Train model
    print("Training model...")
    train_model(model, train_loader, test_loader, criterion, optimizer, EPOCHS, device)

    gcs_uploader = GCSLoader("models-big-data-mini")
    gcs_uploader.upload_from_path("best_model.pth", "best_model.pth")
    gcs_uploader.upload_from_path("scaler_X.json", "scaler_X.json")
    gcs_uploader.upload_from_path("scaler_y.json", "scaler_y.json")
