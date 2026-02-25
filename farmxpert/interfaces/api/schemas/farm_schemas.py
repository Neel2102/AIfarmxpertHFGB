from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Farm schemas
class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    size_acres: float = Field(..., gt=0)
    farmer_name: str = Field(..., min_length=1, max_length=255)
    farmer_phone: Optional[str] = Field(None, max_length=20)
    farmer_email: Optional[str] = Field(None, max_length=255)

class FarmResponse(BaseModel):
    id: int
    name: str
    location: str
    size_acres: float
    farmer_name: str
    farmer_phone: Optional[str]
    farmer_email: Optional[str]
    created_at: datetime

# Task schemas
class TaskCreate(BaseModel):
    crop_id: Optional[int] = None
    task_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_date: datetime
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    assigned_to: Optional[str] = Field(None, max_length=255)
    cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    farm_id: int
    crop_id: Optional[int]
    task_type: str
    title: str
    description: Optional[str]
    scheduled_date: datetime
    completed_date: Optional[datetime]
    priority: str
    status: str
    assigned_to: Optional[str]
    cost: Optional[float]
    notes: Optional[str]
    created_at: datetime

# Crop schemas
class CropCreate(BaseModel):
    field_id: Optional[int] = None
    crop_type: str = Field(..., min_length=1, max_length=100)
    variety: Optional[str] = Field(None, max_length=100)
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    area_acres: float = Field(..., gt=0)
    seed_quantity: Optional[float] = Field(None, ge=0)
    seed_cost: Optional[float] = Field(None, ge=0)
    status: str = Field("planted", pattern="^(planted|growing|harvested)$")
    notes: Optional[str] = None

class CropResponse(BaseModel):
    id: int
    farm_id: int
    field_id: Optional[int]
    crop_type: str
    variety: Optional[str]
    planting_date: Optional[datetime]
    expected_harvest_date: Optional[datetime]
    area_acres: float
    seed_quantity: Optional[float]
    seed_cost: Optional[float]
    status: str
    notes: Optional[str]
    created_at: datetime

# Soil test schemas
class SoilTestCreate(BaseModel):
    field_id: Optional[int] = None
    test_date: datetime
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    nitrogen_ppm: Optional[float] = Field(None, ge=0)
    phosphorus_ppm: Optional[float] = Field(None, ge=0)
    potassium_ppm: Optional[float] = Field(None, ge=0)
    organic_matter_percent: Optional[float] = Field(None, ge=0, le=100)
    soil_texture: Optional[str] = Field(None, max_length=50)
    test_lab: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

class SoilTestResponse(BaseModel):
    id: int
    farm_id: int
    field_id: Optional[int]
    test_date: datetime
    ph_level: Optional[float]
    nitrogen_ppm: Optional[float]
    phosphorus_ppm: Optional[float]
    potassium_ppm: Optional[float]
    organic_matter_percent: Optional[float]
    soil_texture: Optional[str]
    test_lab: Optional[str]
    notes: Optional[str]
    created_at: datetime

# Field schemas
class FieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    size_acres: float = Field(..., gt=0)
    soil_type: Optional[str] = Field(None, max_length=100)
    irrigation_type: Optional[str] = Field(None, max_length=100)

class FieldResponse(BaseModel):
    id: int
    farm_id: int
    name: str
    size_acres: float
    soil_type: Optional[str]
    irrigation_type: Optional[str]
    created_at: datetime

# Yield schemas
class YieldCreate(BaseModel):
    crop_id: int
    harvest_date: datetime
    quantity_tons: float = Field(..., gt=0)
    quality_grade: Optional[str] = Field(None, max_length=20)
    moisture_percent: Optional[float] = Field(None, ge=0, le=100)
    price_per_ton: Optional[float] = Field(None, ge=0)
    total_value: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class YieldResponse(BaseModel):
    id: int
    crop_id: int
    harvest_date: datetime
    quantity_tons: float
    quality_grade: Optional[str]
    moisture_percent: Optional[float]
    price_per_ton: Optional[float]
    total_value: Optional[float]
    notes: Optional[str]
    created_at: datetime

# Weather data schemas
class WeatherDataCreate(BaseModel):
    date: datetime
    temperature_high: Optional[float] = None
    temperature_low: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0, le=100)
    precipitation_mm: Optional[float] = Field(None, ge=0)
    wind_speed_kmh: Optional[float] = Field(None, ge=0)
    wind_direction: Optional[str] = Field(None, max_length=10)
    pressure_hpa: Optional[float] = Field(None, ge=0)
    uv_index: Optional[float] = Field(None, ge=0)
    forecast_data: Optional[dict] = None

class WeatherDataResponse(BaseModel):
    id: int
    farm_id: int
    date: datetime
    temperature_high: Optional[float]
    temperature_low: Optional[float]
    humidity: Optional[float]
    precipitation_mm: Optional[float]
    wind_speed_kmh: Optional[float]
    wind_direction: Optional[str]
    pressure_hpa: Optional[float]
    uv_index: Optional[float]
    forecast_data: Optional[dict]
    created_at: datetime

# Market price schemas
class MarketPriceCreate(BaseModel):
    crop_type: str = Field(..., min_length=1, max_length=100)
    market_location: str = Field(..., min_length=1, max_length=255)
    price_per_ton: float = Field(..., gt=0)
    date: datetime
    source: Optional[str] = Field(None, max_length=255)
    quality_grade: Optional[str] = Field(None, max_length=20)

class MarketPriceResponse(BaseModel):
    id: int
    crop_type: str
    market_location: str
    price_per_ton: float
    date: datetime
    source: Optional[str]
    quality_grade: Optional[str]
    created_at: datetime
