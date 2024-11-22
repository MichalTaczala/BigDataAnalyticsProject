import pandas as pd

from common_models import Location


class AirportData:
    def __init__(self, data_path: str) -> None:
        self._airports = pd.read_csv(data_path)

    def is_airport(self, icao: str) -> bool:
        return icao in self._airports['ident'].values

    def get_location(self, icao: str) -> Location:
        airport = self._airports[self._airports['ident'] == icao]
        return Location(
            latitude=float(airport['latitude'].values[0]),
            longitude=float(airport['longitude'].values[0]),
        )
