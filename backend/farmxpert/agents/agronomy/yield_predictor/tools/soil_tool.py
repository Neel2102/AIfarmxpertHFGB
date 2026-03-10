import requests
from config.settings import SOIL_API_URL
from tools.location_to_latlon import get_lan_lon

def get_soil_data(lat: float, lon: float):
    if not SOIL_API_URL:
        raise ValueError("SOIL_DATA is not set in .env")

    url = SOIL_API_URL.format(lat=lat, lon=lon)
    response = requests.get(url, timeout=20)

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        raise ValueError("Soil API did not return JSON")

# ---- MAIN ----
if __name__ == "__main__":
    location = get_lan_lon("ahmedabad ghatlodia")
    lat = location["latitude"]
    lon = location["longitude"]

    data = get_soil_data(lat, lon)
    print(data)
