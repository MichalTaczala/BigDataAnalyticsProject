from math import radians, sin, cos, sqrt, atan2

#CODE WAS GENERATED USING GPT-4o

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in kilometers
    return distance

def calculate_total_distance_and_time(path):
    total_distance = 0
    total_time = path[-1][0] - path[0][0]  # Total time in seconds (Unix time difference)
    for i in range(1, len(path)):
        prev_point = path[i - 1]
        next_point = path[i]
        total_distance += haversine(prev_point[1], prev_point[2], next_point[1], next_point[2])
    return total_distance, total_time

def calculate_average_velocity(total_distance, total_time):
    if total_time != 0:
        total_distance_m = total_distance * 1000  # Convert distance from kilometers to meters
        average_velocity = total_distance_m / total_time  # Velocity in meters per second
    else:
        average_velocity = 0
    return average_velocity
