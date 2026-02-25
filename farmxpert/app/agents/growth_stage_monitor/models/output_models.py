from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GrowthStageAssessment(BaseModel):
    current_stage: str                  # Germination, Vegetative, Flowering, etc.
    confidence: float                   # 0.0 – 1.0
    estimated_days_in_stage: Optional[int] = None


class GrowthHealthStatus(BaseModel):
    status: str                         # NORMAL, SLOW, ABNORMAL
    deviation_detected: bool
    reason: Optional[str] = None


class GrowthAlert(BaseModel):
    alert_type: str                     # SLOW_GROWTH, STRESS_RISK
    severity: str                       # LOW, MEDIUM, HIGH
    confidence: float
    message: str


class GrowthMonitorOutput(BaseModel):
    stage_assessment: GrowthStageAssessment
    health_status: GrowthHealthStatus
    alerts: List[GrowthAlert] = Field(default_factory=list)
    recommendation: Optional[str] = None
    generated_at: datetime