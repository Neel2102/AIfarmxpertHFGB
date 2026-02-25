"""
Soil Health Agent Output Models
Pydantic models for soil health analysis responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from farmxpert.app.agents.soil_health.models.input_models import SoilSensorData


class SoilIssueType(str, Enum):
    """Types of soil issues that can be detected"""
    ACIDIC_SOIL = "acidic_soil"
    ALKALINE_SOIL = "alkaline_soil"
    HIGH_SALINITY = "high_salinity"
    LOW_NITROGEN = "low_nitrogen"
    LOW_PHOSPHORUS = "low_phosphorus"
    LOW_POTASSIUM = "low_potassium"


class UrgencyLevel(str, Enum):
    """Urgency levels for soil issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SoilIssue(BaseModel):
    """Individual soil issue detected"""
    problem: SoilIssueType = Field(..., description="Type of soil issue")
    cause: str = Field(..., description="Cause of the issue")
    effect: str = Field(..., description="Effect on crops")
    severity: str = Field(..., description="Severity level")
    urgency: UrgencyLevel = Field(..., description="Urgency level for addressing")


class Recommendation(BaseModel):
    """Recommendation for soil improvement"""
    type: str = Field(..., description="Type of recommendation (chemical/organic)")
    name: str = Field(..., description="Name of the recommendation")
    description: str = Field(..., description="Description of the recommendation")
    application_rate: Optional[str] = Field(None, description="Application rate")
    timing: Optional[str] = Field(None, description="When to apply")
    cost_estimate: Optional[str] = Field(None, description="Estimated cost")


class SoilRecommendations(BaseModel):
    """Soil improvement recommendations"""
    chemical: List[Recommendation] = Field(default_factory=list, description="Chemical recommendations")
    organic: List[Recommendation] = Field(default_factory=list, description="Organic recommendations")
    cultural: List[Recommendation] = Field(default_factory=list, description="Cultural practices")


class HealthScoreBreakdown(BaseModel):
    """Breakdown of soil health score components"""
    pH_score: float = Field(..., ge=0, le=100, description="pH component score")
    nutrient_score: float = Field(..., ge=0, le=100, description="Nutrient component score")
    salinity_score: float = Field(..., ge=0, le=100, description="Salinity component score")
    overall_score: float = Field(..., ge=0, le=100, description="Overall health score")


class SoilHealthAnalysis(BaseModel):
    """Main soil health analysis result"""
    agent: str = Field(default="soil_health_agent", description="Agent name")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    location: Dict[str, Any] = Field(..., description="Location information")
    soil_data_analyzed: SoilSensorData = Field(..., description="Soil data used for analysis")
    health_score: HealthScoreBreakdown = Field(..., description="Health score breakdown")
    issues_detected: List[SoilIssue] = Field(default_factory=list, description="Issues detected")
    red_alert: bool = Field(..., description="Whether immediate attention is needed")
    recommendations: SoilRecommendations = Field(..., description="Recommendations for improvement")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class QuickSoilCheckResult(BaseModel):
    """Result of quick soil health check"""
    health_score: float = Field(..., ge=0, le=100, description="Overall health score (0-100)")
    red_alert: bool = Field(..., description="Whether immediate attention is needed")
    issues_count: int = Field(..., ge=0, description="Number of issues detected")
    overall_status: str = Field(..., description="Overall soil status")
    urgency: UrgencyLevel = Field(..., description="Urgency level")
    top_recommendations: List[str] = Field(default_factory=list, description="Top 3 recommendations")
    checked_at: datetime = Field(default_factory=datetime.now, description="Check timestamp")


class SoilHealthResponse(BaseModel):
    """Standard response wrapper for soil health analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis data")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
