import click

import config
from flight_data.airports_data import AirportData
from flight_data.flight_data import FlightData
from data_collection.flight_collector import FlightCollector


@click.command()
@click.option('--days', default=29, help='Days offset from current time')
@click.option('--hours', default=0, help='Hours offset from current time')
def main(days: int, hours: int) -> None:
    airports = AirportData(config.AIRPORTS_DATA)
    flight_data = FlightData(airports)
    collector = FlightCollector(flight_data)
    import datetime
    print(collector.collect_flights_in_time_window(datetime.datetime.now() - datetime.timedelta(hours=2), datetime.datetime.now())[0])
    # collector.run(days, hours)


if __name__ == "__main__":
    main()
