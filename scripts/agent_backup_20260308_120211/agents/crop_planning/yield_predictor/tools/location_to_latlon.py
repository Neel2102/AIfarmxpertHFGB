# @tool
import requests

def get_lan_lon(location:str):
    """
    convert location name into latitude and longitude
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "yield-predictor-agent"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if not data:
        return "Location not found"

    return {
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"])
    }