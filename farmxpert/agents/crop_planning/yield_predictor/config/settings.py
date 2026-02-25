import os 
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_URL = os.getenv("WEATHER_DATA")
SOIL_API_URL = os.getenv("SOIL_DATA")

