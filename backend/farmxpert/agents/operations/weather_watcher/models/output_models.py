from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FarmingAction(BaseModel):
    action: str
    reason: str
    priority: str  # HIGH, MEDIUM, LOW


class RiskAlert(BaseModel):
    alert_type: str          # HEAT_STRESS, HEAVY_RAIN, DRY_SPELL
    severity: str            # LOW, MEDIUM, HIGH
    message: str
    confidence: float        # 0.0 - 1.0


class WeatherSummary(BaseModel):
    temperature: str
    condition: str
    rainfall_outlook: str


class WeatherAlertOutput(BaseModel):
    weather_summary: WeatherSummary
    risk_alerts: List[RiskAlert]
    farming_actions: List[FarmingAction]
    location_info: Optional[dict] = None
    generated_at: datetime


# Legacy model for backward compatibility
class AlertAction(BaseModel):
    action: str
    reason: Optional[str] = None
