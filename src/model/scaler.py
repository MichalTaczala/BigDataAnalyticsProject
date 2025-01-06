from sklearn.preprocessing import StandardScaler
import json
import numpy as np


class Scaler(StandardScaler):
    def save(self, filepath: str) -> None:
        """Save scaler parameters to JSON file"""
        params = {
            'mean': self.mean_.tolist(),
            'scale': self.scale_.tolist(),
            'var': self.var_.tolist(),
            'n_features_in_': self.n_features_in_,
            'n_samples_seen_': int(self.n_samples_seen_)  # Convert np.int64 to int for JSON
        }

        with open(filepath, 'w') as f:
            json.dump(params, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "Scaler":
        """Create a new Scaler instance with parameters loaded from JSON file"""
        with open(filepath, 'r') as f:
            params = json.load(f)

        scaler = cls()
        scaler.mean_ = np.array(params['mean'])
        scaler.scale_ = np.array(params['scale'])
        scaler.var_ = np.array(params['var'])
        scaler.n_features_in_ = params['n_features_in_']
        scaler.n_samples_seen_ = params['n_samples_seen_']

        return scaler
