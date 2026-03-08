import requests
from datetime import datetime, timedelta
from loguru import logger
from ..models.weather_models import WeatherSnapshot, WeatherForecast
from typing import Optional, List
import os
from pathlib import Path
from dotenv import load_dotenv

# Use app configuration instead of manual .env loading
from app.config import settings

# Load project-level .env for backward compatibility
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_PROJECT_ROOT / ".env")

# Use settings for API keys
OPENWEATHER_API_KEY = settings.openweather_api_key or os.getenv("OPENWEATHER_API_KEY")
WEATHERAPI_KEY = settings.weatherapi_key or os.getenv("WEATHERAPI_KEY")


class WeatherService:

    @staticmethod
    def get_weather(latitude: float, longitude: float) -> Optional[WeatherSnapshot]:
        """
        Try OpenWeather first, fallback to WeatherAPI
        """
        weather = WeatherService._fetch_openweather(latitude, longitude)

        if weather:
            return weather

        logger.warning("⚠️ OpenWeather failed, switching to fallback WeatherAPI")
        return WeatherService._fetch_weatherapi(latitude, longitude)

    @staticmethod
    def get_weather_forecast(latitude: float, longitude: float, days: int = 7) -> List[WeatherForecast]:
        """
        Get weather forecast for multiple days
        """
        forecasts = []
        
        # Try OpenWeather forecast first
        try:
            forecasts = WeatherService._fetch_openweather_forecast(latitude, longitude, days)
            if forecasts:
                return forecasts
        except Exception as e:
            logger.warning(f"OpenWeather forecast failed: {e}")
        
        # Fallback to WeatherAPI forecast
        try:
            forecasts = WeatherService._fetch_weatherapi_forecast(latitude, longitude, days)
            if forecasts:
                return forecasts
        except Exception as e:
            logger.error(f"WeatherAPI forecast failed: {e}")
        
        return []

    # ---------------- PRIMARY ---------------- #

    @staticmethod
    def _fetch_openweather(lat: float, lon: float) -> Optional[WeatherSnapshot]:
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            return WeatherSnapshot(
                temperature=data["main"]["temp"],
                min_temperature=data["main"]["temp_min"],
                max_temperature=data["main"]["temp_max"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"] * 3.6,  # m/s → km/h
                rainfall_mm=data.get("rain", {}).get("1h", 0.0),
                rainfall_probability=WeatherService._calculate_rain_probability(data),
                weather_condition=data["weather"][0]["main"].lower(),
                source="OpenWeather",
                observed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"❌ OpenWeather error: {e}")
            return None

    # ---------------- FALLBACK ---------------- #

    # @staticmethod
    # def _fetch_weatherapi(lat: float, lon: float) -> Optional[WeatherSnapshot]:
    #     try:
    #         #url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHERAPI_KEY}"
    #         params = {
    #             "key": WEATHERAPI_KEY,
    #             "q": f"{lat},{lon}"
    #         }

    #         response = requests.get(url, params=params, timeout=10)
    #         response.raise_for_status()

    #         data = response.json()["current"]

    #         return WeatherSnapshot(
    #             temperature=data["temp_c"],
    #             min_temperature=data["temp_c"],
    #             max_temperature=data["temp_c"],
    #             humidity=data["humidity"],
    #             wind_speed=data["wind_kph"],
    #             rainfall_mm=data.get("precip_mm", 0.0),
    #             weather_condition=data["condition"]["text"].lower(),
    #             source="WeatherAPI",
    #             observed_at=datetime.utcnow()
    #         )

    #     except Exception as e:
    #         logger.critical(f"❌ WeatherAPI fallback failed: {e}")
    #         return None

    @staticmethod
    def _fetch_weatherapi(lat: float, lon: float) -> Optional[WeatherSnapshot]:
        try:
            url = "https://api.weatherapi.com/v1/current.json"
            params = {
                "key": WEATHERAPI_KEY,
                "q": f"{lat},{lon}"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()["current"]

            return WeatherSnapshot(
                temperature=data["temp_c"],
                min_temperature=data["temp_c"],
                max_temperature=data["temp_c"],
                humidity=data["humidity"],
                wind_speed=data["wind_kph"],
                rainfall_mm=data.get("precip_mm", 0.0),
                rainfall_probability=WeatherService._calculate_rain_probability_weatherapi(data),
                weather_condition=data["condition"]["text"].lower(),
                source="WeatherAPI",
                observed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.critical(f"❌ WeatherAPI fallback failed: {e}")
            return None

    # ---------------- FORECAST METHODS ---------------- #

    @staticmethod
    def _fetch_openweather_forecast(lat: float, lon: float, days: int) -> List[WeatherForecast]:
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            forecasts = []

            # Process daily forecasts (take midday forecast for each day)
            for i in range(0, min(len(data["list"]), days * 8), 8):
                if i < len(data["list"]):
                    forecast_data = data["list"][i]
                    forecasts.append(WeatherForecast(
                        date=datetime.fromtimestamp(forecast_data["dt"]),
                        temperature=forecast_data["main"]["temp"],
                        min_temperature=forecast_data["main"]["temp_min"],
                        max_temperature=forecast_data["main"]["temp_max"],
                        humidity=forecast_data["main"]["humidity"],
                        wind_speed=forecast_data["wind"]["speed"] * 3.6,
                        rainfall_mm=forecast_data.get("rain", {}).get("3h", 0.0),
                        rainfall_probability=forecast_data.get("pop", 0.0),
                        weather_condition=forecast_data["weather"][0]["main"].lower(),
                        source="OpenWeather"
                    ))
            
            return forecasts

        except Exception as e:
            logger.error(f"❌ OpenWeather forecast error: {e}")
            return []

    @staticmethod
    def _fetch_weatherapi_forecast(lat: float, lon: float, days: int) -> List[WeatherForecast]:
        try:
            url = "https://api.weatherapi.com/v1/forecast.json"
            params = {
                "key": WEATHERAPI_KEY,
                "q": f"{lat},{lon}",
                "days": min(days, 10)  # WeatherAPI supports up to 10 days
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            forecasts = []

            for day_data in data["forecast"]["forecastday"]:
                forecasts.append(WeatherForecast(
                    date=datetime.fromisoformat(day_data["date"]),
                    temperature=day_data["day"]["avgtemp_c"],
                    min_temperature=day_data["day"]["mintemp_c"],
                    max_temperature=day_data["day"]["maxtemp_c"],
                    humidity=day_data["day"]["avghumidity"],
                    wind_speed=day_data["day"]["maxwind_kph"],
                    rainfall_mm=day_data["day"]["totalprecip_mm"],
                    rainfall_probability=day_data["day"]["daily_chance_of_rain"] / 100.0,
                    weather_condition=day_data["day"]["condition"]["text"].lower(),
                    source="WeatherAPI"
                ))
            
            return forecasts

        except Exception as e:
            logger.error(f"❌ WeatherAPI forecast error: {e}")
            return []

    # ---------------- UTILITY METHODS ---------------- #

    @staticmethod
    def _calculate_rain_probability(data: dict) -> float:
        """Calculate rain probability from OpenWeather data"""
        # Use precipitation probability if available
        if "pop" in data:
            return data["pop"]
        
        # Estimate based on weather condition and humidity
        condition = data.get("weather", [{}])[0].get("main", "").lower()
        humidity = data.get("main", {}).get("humidity", 0)
        
        if condition in ["rain", "drizzle", "thunderstorm"]:
            return 0.8
        elif condition in ["clouds", "mist", "fog"]:
            return min(0.4, humidity / 100.0)
        else:
            return 0.1

    @staticmethod
    def _calculate_rain_probability_weatherapi(data: dict) -> float:
        """Calculate rain probability from WeatherAPI data"""
        # WeatherAPI provides precipitation data directly
        precip_mm = data.get("precip_mm", 0.0)
        condition = data.get("condition", {}).get("text", "").lower()
        humidity = data.get("humidity", 0)
        
        if precip_mm > 0:
            return min(1.0, precip_mm / 10.0)  # Scale by precipitation amount
        elif "rain" in condition or "drizzle" in condition or "thunder" in condition:
            return 0.7
        elif "cloud" in condition or "mist" in condition or "fog" in condition:
            return min(0.3, humidity / 100.0)
        else:
            return 0.05
