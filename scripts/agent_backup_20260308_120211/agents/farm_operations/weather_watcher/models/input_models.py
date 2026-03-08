from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationInput(BaseModel):
    latitude: float
    longitude: float
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"


class CropContext(BaseModel):
    crop_name: Optional[str] = None
    growth_stage: Optional[str] = None


class WeatherWatcherInput(BaseModel):
    location: LocationInput
    crop: Optional[CropContext] = None
    triggered_at: datetime
    check_type: str  # "CRITICAL" or "NORMAL"
