import requests
from typing import Dict, Any, Optional, List
from farmxpert.config.settings import settings
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class WeatherClientTool:
    """
    Client for OpenWeatherMap API to fetch real weather forecasts.
    Falls back to simulated data if API key is missing or requests fail.
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"
    CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"

    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Fetch current weather for a location"""
        api_key = settings.openweather_api_key
        
        if not api_key:
            logger.warning("No OpenWeather API key found. Using simulated data.")
            return self._get_simulated_current_weather(location)

        try:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }
            response = requests.get(self.CURRENT_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_weather_response(data)
            else:
                logger.warning(f"Weather API error {response.status_code}: {response.text}")
                return self._get_simulated_current_weather(location)
                
        except Exception as e:
            logger.error(f"Weather client connection error: {e}")
            return self._get_simulated_current_weather(location)

    def get_forecast(self, location: str) -> Dict[str, Any]:
        """Fetch 5-day forecast"""
        api_key = settings.openweather_api_key
        
        if not api_key:
            return self._get_simulated_forecast(location)

        try:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return self._get_simulated_forecast(location)
        except Exception:
            return self._get_simulated_forecast(location)

    def _format_weather_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format API response to standard structure"""
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "location": data["name"],
            "source": "OpenWeatherMap"
        }

    def _get_simulated_current_weather(self, location: str) -> Dict[str, Any]:
        """Generate realistic simulated weather"""
        # Simple season logic
        month = datetime.now().month
        is_monsoon = 6 <= month <= 9
        is_winter = 11 <= month <= 2
        
        temp = 32.0
        humidity = 40
        condition = "Sunny"
        
        if is_monsoon:
            temp = random.uniform(25, 30)
            humidity = random.uniform(70, 95)
            condition = random.choice(["Rainy", "Cloudy", "Drizzle"])
        elif is_winter:
            temp = random.uniform(10, 25)
            humidity = random.uniform(30, 60)
            condition = "Clear"
        else:
            temp = random.uniform(30, 42)
            humidity = random.uniform(20, 50)
        
        return {
            "temp": round(temp, 1),
            "humidity": int(humidity),
            "condition": condition,
            "wind_speed": round(random.uniform(5, 15), 1),
            "location": location,
            "source": "Simulated (No API Key)"
        }

    def _get_simulated_forecast(self, location: str) -> Dict[str, Any]:
        """Generate simulated 5-day forecast"""
        forecast = []
        base = self._get_simulated_current_weather(location)
        
        for i in range(5):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            # slight variation
            temp = base["temp"] + random.uniform(-2, 2)
            forecast.append({
                "date": date,
                "temp": round(temp, 1),
                "condition": base["condition"],
                "humidity": base["humidity"]
            })
            
        return {"list": forecast, "city": {"name": location}, "source": "Simulated"}
