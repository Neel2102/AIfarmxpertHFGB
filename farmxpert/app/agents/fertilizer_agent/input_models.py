"""
Input Models for Fertilizer Advisor Agent

Designed for multi-agent orchestration where:
- Orchestrator routes data between agents
- Each agent is independent and advisory
- Communication happens strictly via typed models
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SoilContext(BaseModel):
    """Soil nutrient context in kg/acre"""
    nitrogen_kg_per_acre: float = Field(..., ge=0, description="Soil nitrogen content (N) in kg/acre")
    phosphorus_kg_per_acre: float = Field(..., ge=0, description="Soil phosphorus content (P) in kg/acre") 
    potassium_kg_per_acre: float = Field(..., ge=0, description="Soil potassium content (K) in kg/acre")


class WeatherContext(BaseModel):
    """Weather context for safety validation"""
    rainfall_last_3_days_mm: float = Field(..., ge=0, description="Total rainfall in last 3 days (mm)")
    forecast_next_5_days: list[str] = Field(..., description="Weather forecast for next 5 days")
    temperature_celsius: Optional[float] = Field(None, description="Current temperature (°C)")
    humidity_percent: Optional[float] = Field(None, ge=0, le=100, description="Current humidity (%)")


class TriggerMetadata(BaseModel):
    """Metadata about what triggered this advisory request"""
    triggered_at: datetime = Field(..., description="When the request was triggered")
    trigger_source: Literal["manual", "sensor", "orchestrator"] = Field(..., description="Source of the trigger")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")


class FertilizerAdvisorInput(BaseModel):
    """
    Complete input model for Fertilizer Advisor Agent
    
    This model is designed to be populated by:
    - Direct farmer input
    - Sensor data
    - Other agents (Growth Stage Monitor, Weather Watcher)
    
    The agent does NOT infer growth stage or call other agents internally.
    It processes the provided data and returns advisory recommendations.
    """
    
    # Identity Context
    farmer_id: str = Field(..., description="Unique identifier for the farmer")
    field_id: str = Field(..., description="Unique identifier for the field")
    
    # Crop Context
    crop_name: str = Field(..., description="Crop name (e.g., 'wheat', 'cotton')")
    growth_stage: str = Field(..., description="Growth stage as received (e.g., 'tillering', 'flowering')")
    
    # Field Context
    area_acres: float = Field(..., gt=0, description="Field area in acres")
    
    # Soil Context
    soil: SoilContext = Field(..., description="Current soil nutrient status")
    
    # Weather Context
    weather: WeatherContext = Field(..., description="Current and forecast weather conditions")
    
    # Trigger Metadata
    trigger: TriggerMetadata = Field(..., description="Request trigger information")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "farmer_id": "farmer_001",
                "field_id": "field_alpha",
                "crop_name": "wheat",
                "growth_stage": "tillering",
                "area_acres": 2.5,
                "soil": {
                    "nitrogen_kg_per_acre": 12.0,
                    "phosphorus_kg_per_acre": 8.0,
                    "potassium_kg_per_acre": 15.0
                },
                "weather": {
                    "rainfall_last_3_days_mm": 5.0,
                    "forecast_next_5_days": ["sunny", "sunny", "cloudy", "sunny", "sunny"],
                    "temperature_celsius": 25.0,
                    "humidity_percent": 65.0
                },
                "trigger": {
                    "triggered_at": "2026-01-29T16:30:00Z",
                    "trigger_source": "orchestrator",
                    "request_id": "req_12345"
                }
            }
        }
    }
