import math


#distance in km between two GPS points
def haversine_km(lat1, lng1, lat2, lng2):
    # Earth radius in kilometers
    R = 6371.0

    # convert degrees -> radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    # haversine formula
    a = (math.sin(d_phi / 2) ** 2) + (math.cos(phi1) * math.cos(phi2) * (math.sin(d_lambda / 2) ** 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
