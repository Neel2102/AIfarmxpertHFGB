"""
Input models for Market Intelligence Agent - Main Project Integration
Simplified models for FastAPI integration
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class QuickAnalysisRequest(BaseModel):
    """Request model for quick market analysis"""
    crop: str = Field(..., description="Crop name")
    state: str = Field(..., description="State name")
    area_hectares: Optional[float] = Field(None, description="Farm area in hectares")
    expected_yield_quintals_per_hectare: Optional[float] = Field(None, description="Expected yield per hectare")
    district: Optional[str] = Field(None, description="District name")


class CropInfoRequest(BaseModel):
    """Crop information for comprehensive analysis"""
    name: str = Field(..., description="Crop name")
    variety: Optional[str] = Field(None, description="Crop variety")
    season: Optional[str] = Field(None, description="Growing season")
    grade: Optional[str] = Field(None, description="Crop grade")


class LocationInfoRequest(BaseModel):
    """Location information for comprehensive analysis"""
    state: str = Field(..., description="State name")
    district: Optional[str] = Field(None, description="District name")
    tehsil: Optional[str] = Field(None, description="Tehsil name")
    village: Optional[str] = Field(None, description="Village name")
    pincode: Optional[str] = Field(None, description="PIN code")


class FarmInfoRequest(BaseModel):
    """Farm information for comprehensive analysis"""
    area_hectares: float = Field(..., description="Farm area in hectares")
    expected_yield_quintals_per_hectare: float = Field(..., description="Expected yield per hectare")
    irrigation_type: Optional[str] = Field(None, description="Irrigation type")
    soil_type: Optional[str] = Field(None, description="Soil type")
    cultivation_method: Optional[str] = Field(None, description="Cultivation method")


class MarketPreferencesRequest(BaseModel):
    """Market analysis preferences"""
    analysis_type: Optional[str] = Field("comprehensive", description="Analysis type")
    include_risk_analysis: Optional[bool] = Field(True, description="Include risk analysis")
    max_markets_to_analyze: Optional[int] = Field(20, description="Maximum markets to analyze")
    confidence_threshold: Optional[float] = Field(0.7, description="Confidence threshold")


class ComprehensiveAnalysisRequest(BaseModel):
    """Request model for comprehensive market analysis"""
    crop_info: CropInfoRequest = Field(..., description="Crop information")
    location: LocationInfoRequest = Field(..., description="Location information")
    farm_info: FarmInfoRequest = Field(..., description="Farm information")
    preferences: Optional[MarketPreferencesRequest] = Field(None, description="Analysis preferences")


class MarketAnalysisResponse(BaseModel):
    """Response model for market analysis"""
    success: bool = Field(..., description="Request success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class AgentInfoResponse(BaseModel):
    """Response model for agent information"""
    name: str
    version: str
    capabilities: list
    supported_crops: list
    supported_states: list
    data_sources: list
