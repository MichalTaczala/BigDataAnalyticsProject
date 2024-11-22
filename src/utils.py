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
