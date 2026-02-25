"""
Input Models - Data models for crop advisor system inputs
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class Season(Enum):
    KHARIF = "Kharif"
    RABI = "Rabi"
    ZAID = "Zaid"


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RainfallOutlook(Enum):
    BELOW = "Below"
    NORMAL = "Normal"
    ABOVE = "Above"


class TemperatureTrend(Enum):
    COOL = "Cool"
    MODERATE = "Moderate"
    WARM = "Warm"
    HOT = "Hot"


class WaterAvailability(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class IrrigationReliability(Enum):
    POOR = "Poor"
    MODERATE = "Moderate"
    GOOD = "Good"


class SoilType(Enum):
    CLAY = "Clay"
    LOAMY = "Loamy"
    SANDY = "Sandy"
    RED_LOAMY = "Red Loamy"
    SANDY_LOAM = "Sandy Loam"


class FertilityLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class MarketTrend(Enum):
    STABLE = "Stable"
    RISING = "Rising"
    FALLING = "Falling"


class MarketVolatility(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class PestPressure(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass
class Location:
    """Location information"""
    state: str
    district: str
    village: Optional[str] = None
    pincode: Optional[str] = None


@dataclass
class FarmerContext:
    """Farmer context input model"""
    location: Location
    season: Season
    land_size_acre: float
    risk_preference: RiskLevel
    farmer_id: Optional[str] = None
    contact_number: Optional[str] = None


@dataclass
class WeatherInput:
    """Weather agent input model"""
    rainfall_outlook: RainfallOutlook
    temperature_trend: TemperatureTrend
    dry_spell_risk: str  # Low/Medium/High
    heat_stress_risk: str  # Low/Medium/High
    pest_pressure: PestPressure
    pest_alerts: List[str]
    high_risk_crops: List[str]
    monsoon_onset: Optional[str] = None  # Not applicable in Feb


@dataclass
class SoilHealthInput:
    """Soil health agent input model"""
    soil_type: SoilType
    fertility: FertilityLevel
    ph_level: str  # Acidic/Neutral/Alkaline
    organic_matter: str  # Low/Medium/High
    water_holding_capacity: str  # Low/Medium/High


@dataclass
class IrrigationInput:
    """Irrigation planner input model"""
    water_availability: WaterAvailability
    irrigation_reliability: IrrigationReliability
    groundwater_level: str  # Low/Medium/High/Stable
    canal_supply: str  # Minimal/Reduced/Adequate/Good


@dataclass
class FertilizerInput:
    """Fertilizer agent input model"""
    nutrient_status: str  # Depleted/Low/Balanced/Good
    recommended_npk: str
    soil_fertility_index: str  # Low/Medium/High
    organic_matter_required: str  # Low/Medium/High/Very High


@dataclass
class MarketInput:
    """Market intelligence input model"""
    price_trend: MarketTrend
    market_volatility: MarketVolatility
    demand_forecast: str  # Stable/Increasing/Decreasing
    msp_supported_crops: List[str]
    insurance_supported_crops: List[str]
    subsidy_favored_crops: List[str]
    price_stability: Dict[str, str]  # crop -> stability level


@dataclass
class CropAdvisorInput:
    """Complete input model for crop advisor"""
    farmer_context: FarmerContext
    weather_watcher: WeatherInput
    soil_health: SoilHealthInput
    irrigation_planner: IrrigationInput
    fertilizer_agent: FertilizerInput
    market_intelligence: MarketInput
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "farmer_context": {
                "location": asdict(self.farmer_context.location),
                "season": self.farmer_context.season.value,
                "land_size_acre": self.farmer_context.land_size_acre,
                "risk_preference": self.farmer_context.risk_preference.value,
                "farmer_id": self.farmer_context.farmer_id,
                "contact_number": self.farmer_context.contact_number
            },
            "weather_watcher": {
                "rainfall_outlook": self.weather_watcher.rainfall_outlook.value,
                "temperature_trend": self.weather_watcher.temperature_trend.value,
                "dry_spell_risk": self.weather_watcher.dry_spell_risk,
                "heat_stress_risk": self.weather_watcher.heat_stress_risk,
                "pest_pressure": self.weather_watcher.pest_pressure.value,
                "pest_alerts": self.weather_watcher.pest_alerts,
                "high_risk_crops": self.weather_watcher.high_risk_crops,
                "monsoon_onset": self.weather_watcher.monsoon_onset
            },
            "soil_health": {
                "soil_type": self.soil_health.soil_type.value,
                "fertility": self.soil_health.fertility.value,
                "ph_level": self.soil_health.ph_level,
                "organic_matter": self.soil_health.organic_matter,
                "water_holding_capacity": self.soil_health.water_holding_capacity
            },
            "irrigation_planner": {
                "water_availability": self.irrigation_planner.water_availability.value,
                "irrigation_reliability": self.irrigation_planner.irrigation_reliability.value,
                "groundwater_level": self.irrigation_planner.groundwater_level,
                "canal_supply": self.irrigation_planner.canal_supply
            },
            "fertilizer_agent": {
                "nutrient_status": self.fertilizer_agent.nutrient_status,
                "recommended_npk": self.fertilizer_agent.recommended_npk,
                "soil_fertility_index": self.fertilizer_agent.soil_fertility_index,
                "organic_matter_required": self.fertilizer_agent.organic_matter_required
            },
            "market_intelligence": {
                "price_trend": self.market_intelligence.price_trend.value,
                "market_volatility": self.market_intelligence.market_volatility.value,
                "demand_forecast": self.market_intelligence.demand_forecast,
                "msp_supported_crops": self.market_intelligence.msp_supported_crops,
                "insurance_supported_crops": self.market_intelligence.insurance_supported_crops,
                "subsidy_favored_crops": self.market_intelligence.subsidy_favored_crops,
                "price_stability": self.market_intelligence.price_stability
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CropAdvisorInput':
        """Create from dictionary"""
        return cls(
            farmer_context=FarmerContext(
                location=Location(**data["farmer_context"]["location"]),
                season=Season(data["farmer_context"]["season"]),
                land_size_acre=data["farmer_context"]["land_size_acre"],
                risk_preference=RiskLevel(data["farmer_context"]["risk_preference"]),
                farmer_id=data["farmer_context"].get("farmer_id"),
                contact_number=data["farmer_context"].get("contact_number")
            ),
            weather_watcher=WeatherInput(
                rainfall_outlook=RainfallOutlook(data["weather_watcher"]["rainfall_outlook"]),
                temperature_trend=TemperatureTrend(data["weather_watcher"]["temperature_trend"]),
                dry_spell_risk=data["weather_watcher"]["dry_spell_risk"],
                heat_stress_risk=data["weather_watcher"]["heat_stress_risk"],
                pest_pressure=PestPressure(data["weather_watcher"]["pest_pressure"]),
                pest_alerts=data["weather_watcher"]["pest_alerts"],
                high_risk_crops=data["weather_watcher"]["high_risk_crops"],
                monsoon_onset=data["weather_watcher"].get("monsoon_onset")
            ),
            soil_health=SoilHealthInput(
                soil_type=SoilType(data["soil_health"]["soil_type"]),
                fertility=FertilityLevel(data["soil_health"]["fertility"]),
                ph_level=data["soil_health"]["ph_level"],
                organic_matter=data["soil_health"]["organic_matter"],
                water_holding_capacity=data["soil_health"]["water_holding_capacity"]
            ),
            irrigation_planner=IrrigationInput(
                water_availability=WaterAvailability(data["irrigation_planner"]["water_availability"]),
                irrigation_reliability=IrrigationReliability(data["irrigation_planner"]["irrigation_reliability"]),
                groundwater_level=data["irrigation_planner"]["groundwater_level"],
                canal_supply=data["irrigation_planner"]["canal_supply"]
            ),
            fertilizer_agent=FertilizerInput(
                nutrient_status=data["fertilizer_agent"]["nutrient_status"],
                recommended_npk=data["fertilizer_agent"]["recommended_npk"],
                soil_fertility_index=data["fertilizer_agent"]["soil_fertility_index"],
                organic_matter_required=data["fertilizer_agent"]["organic_matter_required"]
            ),
            market_intelligence=MarketInput(
                price_trend=MarketTrend(data["market_intelligence"]["price_trend"]),
                market_volatility=MarketVolatility(data["market_intelligence"]["market_volatility"]),
                demand_forecast=data["market_intelligence"]["demand_forecast"],
                msp_supported_crops=data["market_intelligence"]["msp_supported_crops"],
                insurance_supported_crops=data["market_intelligence"]["insurance_supported_crops"],
                subsidy_favored_crops=data["market_intelligence"]["subsidy_favored_crops"],
                price_stability=data["market_intelligence"]["price_stability"]
            )
        )
