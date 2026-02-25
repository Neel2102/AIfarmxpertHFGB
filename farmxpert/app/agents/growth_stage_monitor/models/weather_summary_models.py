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
