from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class WeatherSummary(BaseModel):
    location_id: str
    start_date: str
    end_date: str

    avg_temperature: float
    total_rainfall_mm: float

    heat_stress_days: int
    heavy_rain_days: int
    dry_days: int

    confidence: float


class WeatherSnapshot(BaseModel):
    temperature: float          # °C
    min_temperature: float      # °C
    max_temperature: float      # °C
    humidity: int               # %
    wind_speed: float           # km/h
    rainfall_mm: float          # mm
    rainfall_probability: float # 0.0 - 1.0 (probability of rain)
    weather_condition: str      # rain, clear, clouds, etc.
    source: str                 # OpenWeather / WeatherAPI
    observed_at: datetime


class WeatherForecast(BaseModel):
    date: datetime
    temperature: float          # °C
    min_temperature: float      # °C
    max_temperature: float      # °C
    humidity: int               # %
    wind_speed: float           # km/h
    rainfall_mm: float          # mm
    rainfall_probability: float # 0.0 - 1.0 (probability of rain)
    weather_condition: str      # rain, clear, clouds, etc.
    source: str                 # OpenWeather / WeatherAPI
