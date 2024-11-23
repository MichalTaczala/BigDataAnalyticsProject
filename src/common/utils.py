from datetime import datetime, timezone


def calculate_speed(distance: float, time: float) -> float | None:
    """
    Calculate speed in km/h

    :param distance: distance in kilometers
    :param time: time in seconds
    :return: speed in km/h or None if time is 0
    """

    if time != 0:
        return abs(distance / (time / 3600))
    return None


def interpolate_value(start: float, end: float, progress: float) -> float:
    """
    Linearly interpolates between two values given a progress value.

    :param start: start value
    :param end: end value
    :param progress: progress between 0 and 1
    :return: interpolated value rounded to 2 decimal places
    """

    return round(start + progress * (end - start), 2)


def timestamp_to_date(timestamp: int) -> str:
    """
    Convert timestamp in seconds since epoch to date in the format "YYYY-MM-DD".

    :param timestamp: timestamp in seconds since epoch
    :return: date in the format "YYYY-MM-DD"
    """

    return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")
