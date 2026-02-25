"""
Soil Health Agent Input Models
Pydantic models for soil health analysis requests
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class LocationInput(BaseModel):
    """Location information for soil analysis"""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    district: Optional[str] = Field(None, description="District name")
    state: Optional[str] = Field(None, description="State name")
    field_id: Optional[str] = Field(None, description="Field identifier")


class SoilSensorData(BaseModel):
    """Soil sensor measurements"""
    pH: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)")
    nitrogen: float = Field(..., ge=0.0, description="Nitrogen content in ppm")
    phosphorus: float = Field(..., ge=0.0, description="Phosphorus content in ppm")
    potassium: float = Field(..., ge=0.0, description="Potassium content in ppm")
    electrical_conductivity: float = Field(..., ge=0.0, description="Electrical conductivity in dS/m")
    moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture percentage")
    temperature: Optional[float] = Field(None, description="Soil temperature in Celsius")
    organic_matter: Optional[float] = Field(None, ge=0.0, le=100.0, description="Organic matter percentage")


class SoilHealthInput(BaseModel):
    """Main input model for soil health analysis"""
    location: LocationInput
    soil_data: SoilSensorData
    crop_type: Optional[str] = Field(None, description="Current crop type")
    growth_stage: Optional[str] = Field(None, description="Current growth stage")
    triggered_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    request_source: str = Field(default="api", description="Source of the request")
    field_id: Optional[str] = Field(None, description="Field identifier")


class QuickSoilCheckInput(BaseModel):
    """Simplified input for quick soil health check"""
    pH: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)")
    nitrogen: float = Field(..., ge=0.0, description="Nitrogen content in ppm")
    phosphorus: float = Field(..., ge=0.0, description="Phosphorus content in ppm")
    potassium: float = Field(..., ge=0.0, description="Potassium content in ppm")
    electrical_conductivity: float = Field(..., ge=0.0, description="Electrical conductivity in dS/m")
    moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture percentage")
    temperature: Optional[float] = Field(None, description="Soil temperature in Celsius")
