import requests
from config.settings import WEATHER_API_URL

def get_weather_data(lat: float, lon: float):
    if not WEATHER_API_URL:
        raise ValueError("WEATHER_DATA is not set in .env")
    params = {
        'latitude': lat,
        'longitude': lon,
        'current_weather': True
    }
    response = requests.get(WEATHER_API_URL, params=params, timeout=20)
    data = response.json()

    # Handle API error
    if 'current_weather' not in data:
        raise ValueError(f"API error: {data}")

    return {
        "temperature": data["current_weather"]["temperature"],
        "windspeed": data["current_weather"]["windspeed"]
    }