from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    district: Optional[str] = Field(None, description="District")
    state: Optional[str] = Field(None, description="State")
    field_id: Optional[str] = Field(None, description="Field identifier")


class SoilSensorData(BaseModel):
    pH: float = Field(..., description="Soil pH")
    nitrogen: float = Field(..., description="Nitrogen (ppm)")
    phosphorus: float = Field(..., description="Phosphorus (ppm)")
    potassium: float = Field(..., description="Potassium (ppm)")
    electrical_conductivity: float = Field(..., description="Electrical conductivity (dS/m)")
    moisture: Optional[float] = Field(None, description="Soil moisture (%)")
    temperature: Optional[float] = Field(None, description="Soil temperature (°C)")
    organic_matter: Optional[float] = Field(None, description="Organic matter (%)")


class SoilHealthInput(BaseModel):
    location: LocationInput
    soil_data: SoilSensorData
    crop_type: Optional[str] = None
    growth_stage: Optional[str] = None
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    request_source: Optional[str] = None
    field_id: Optional[str] = None


class QuickSoilCheckInput(BaseModel):
    pH: float = 7.0
    nitrogen: float = 50.0
    phosphorus: float = 20.0
    potassium: float = 100.0
    electrical_conductivity: float = 1.0
    moisture: Optional[float] = None
    temperature: Optional[float] = None
