"""
Output Models for Fertilizer Advisor Agent

Designed for multi-agent orchestration where:
- Output is deterministic and explainable
- Orchestrator can compare, suppress, or merge recommendations
- Safety blocks and confidence are explicit and machine-readable
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class RDFSource(str, Enum):
    """Source of crop RDF data"""
    EXACT = "exact"      # From master crop database
    GROUP = "group"      # From crop group fallback
    GENERIC = "generic"  # From generic fallback


class NutrientType(str, Enum):
    """Supported nutrient types"""
    NITROGEN = "N"
    PHOSPHORUS = "P2O5"
    POTASSIUM = "K2O"


class FertilizerRecommendation(BaseModel):
    """
    Individual fertilizer recommendation with full context
    
    Each recommendation is self-contained and can be:
    - Compared with other agent recommendations
    - Suppressed by orchestrator if conflicts exist
    - Merged with similar recommendations from other agents
    """
    nutrient_type: NutrientType = Field(..., description="Nutrient being addressed")
    fertilizer_name: str = Field(..., description="Recommended fertilizer product")
    dose_per_acre_kg: float = Field(..., gt=0, description="Dose per acre in kilograms")
    total_quantity_kg: float = Field(..., gt=0, description="Total quantity for the field")
    application_method: str = Field(..., description="How to apply the fertilizer")
    timing: str = Field(..., description="When to apply (e.g., 'After irrigation')")
    reason: str = Field(..., description="Why this fertilizer is recommended")
    rdf_source: RDFSource = Field(..., description="Source of RDF data used")
    recommendation_confidence: float = Field(..., ge=0, le=1, description="Confidence in this specific recommendation")
    safety_notes: List[str] = Field(default_factory=list, description="Safety-related notes")
    
    

class AgentStatus(str, Enum):
    """Agent operational status"""
    OK = "ok"
    BLOCKED = "blocked"


class FertilizerAdvisorOutput(BaseModel):
    """
    Complete output model for Fertilizer Advisor Agent
    
    This output is designed for orchestrator consumption:
    - Clear status for decision routing
    - Explicit blockers for safety enforcement
    - Structured recommendations for comparison/merging
    - Confidence scoring for prioritization
    """
    
    # Agent Identity
    agent_name: str = Field(default="fertilizer_advisor", description="Name of the generating agent")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When this response was generated")
    
    # Status and Safety
    status: AgentStatus = Field(..., description="Overall agent status")
    blockers: List[str] = Field(default_factory=list, description="Reasons why application is blocked")
    
    # Recommendations
    recommendations: List[FertilizerRecommendation] = Field(
        default_factory=list, 
        description="Fertilizer recommendations (empty if blocked or no deficits)"
    )
    
    # Additional Information
    alerts: List[str] = Field(default_factory=list, description="Non-blocking warnings or information")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence in the advisory")
    
    # Request Context
    request_id: Optional[str] = Field(None, description="Original request ID for traceability")
    farmer_id: Optional[str] = Field(None, description="Farmer ID from input")
    field_id: Optional[str] = Field(None, description="Field ID from input")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "agent_name": "fertilizer_advisor",
                "generated_at": "2026-01-29T16:30:15Z",
                "status": "ok",
                "blockers": [],
                "recommendations": [
                    {
                        "nutrient_type": "N",
                        "fertilizer_name": "nitrogen_source",
                        "dose_per_acre_kg": 11.2,
                        "total_quantity_kg": 28.0,
                        "application_method": "After irrigation",
                        "timing": "Within 3 days",
                        "reason": "Nitrogen deficit at tillering stage",
                        "rdf_source": "exact",
                        "recommendation_confidence": 0.85,
                        "safety_notes": []
                    }
                ],
                "alerts": ["Soil moisture is low - consider irrigation before application"],
                "confidence": 0.85,
                "request_id": "req_12345",
                "farmer_id": "farmer_001",
                "field_id": "field_alpha"
            }
        }
    }


# Convenience factory for blocked responses
def create_blocked_response(
    blockers: List[str],
    request_id: Optional[str] = None,
    farmer_id: Optional[str] = None,
    field_id: Optional[str] = None
) -> FertilizerAdvisorOutput:
    """Create a blocked response with zero confidence"""
    return FertilizerAdvisorOutput(
        status=AgentStatus.BLOCKED,
        blockers=blockers,
        confidence=0.0,
        request_id=request_id,
        farmer_id=farmer_id,
        field_id=field_id
    )


# Convenience factory for OK responses
def create_ok_response(
    recommendations: List[FertilizerRecommendation],
    confidence: float,
    alerts: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    farmer_id: Optional[str] = None,
    field_id: Optional[str] = None
) -> FertilizerAdvisorOutput:
    """Create an OK response with recommendations"""
    return FertilizerAdvisorOutput(
        status=AgentStatus.OK,
        recommendations=recommendations,
        alerts=alerts or [],
        confidence=confidence,
        request_id=request_id,
        farmer_id=farmer_id,
        field_id=field_id
    )
