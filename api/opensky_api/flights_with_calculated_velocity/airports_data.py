import pandas as pd


class AirportData:
    def __init__(self, data_path: str):
        self._airports = pd.read_csv(data_path)

    def is_airport(self, icao: str) -> bool:
        return icao in self._airports['ident'].values

    def get_location(self, icao: str) -> tuple[float, float]:
        airport = self._airports[self._airports['ident'] == icao]
        return float(airport['latitude'].values[0]), float(airport['longitude'].values[0])
