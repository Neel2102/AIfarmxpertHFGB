"""
Validation and utilities for crop advisor system
"""

from typing import List, Dict, Any
from .input import CropAdvisorInput
from data.february_data import get_february_data


def validate_input(input_data: CropAdvisorInput) -> List[str]:
    """Validate input data and return list of errors"""
    errors = []
    
    # Validate farmer context
    if input_data.farmer_context.land_size_acre <= 0:
        errors.append("Land size must be positive")
    
    if input_data.farmer_context.land_size_acre > 1000:
        errors.append("Land size seems unrealistic (>1000 acres)")
    
    # Validate season and location consistency
    if input_data.farmer_context.season.value == "Kharif" and input_data.weather_watcher.monsoon_onset is None:
        errors.append("Monsoon onset required for Kharif season")
    
    # Validate water availability and irrigation consistency
    if (input_data.irrigation_planner.water_availability.value == "HIGH" and 
        input_data.irrigation_planner.irrigation_reliability.value == "POOR"):
        errors.append("High water availability with poor irrigation reliability is inconsistent")
    
    # Validate soil and fertilizer consistency
    if (input_data.soil_health.fertility.value == "HIGH" and 
        input_data.fertilizer_agent.nutrient_status == "Very Low"):
        errors.append("High soil fertility with very low nutrient status is inconsistent")
    
    # Validate market data
    if not input_data.market_intelligence.msp_supported_crops:
        errors.append("At least one MSP supported crop should be listed")
    
    return errors


def create_sample_input(state: str = "Punjab", district: str = "Ludhiana") -> CropAdvisorInput:
    """Create sample input for testing"""
    
    # Get February data
    feb_data = get_february_data(state)
    
    # Import enums from input module
    from .input import (
        Season, RiskLevel, Location, FarmerContext,
        WeatherInput, RainfallOutlook, TemperatureTrend, PestPressure,
        SoilHealthInput, SoilType, FertilityLevel,
        IrrigationInput, WaterAvailability, IrrigationReliability,
        FertilizerInput, MarketInput, MarketTrend, MarketVolatility
    )
    
    # Create structured input
    return CropAdvisorInput(
        farmer_context=FarmerContext(
            location=Location(state=state, district=district),
            season=Season.RABI,
            land_size_acre=5.0,
            risk_preference=RiskLevel.MEDIUM
        ),
        weather_watcher=WeatherInput(
            rainfall_outlook=RainfallOutlook(feb_data["weather_watcher"]["rainfall_outlook"]),
            temperature_trend=TemperatureTrend(feb_data["weather_watcher"]["temperature_trend"]),
            dry_spell_risk=feb_data["weather_watcher"]["dry_spell_risk"],
            heat_stress_risk=feb_data["weather_watcher"]["heat_stress_risk"],
            pest_pressure=PestPressure(feb_data["weather_watcher"]["pest_pressure"]),
            pest_alerts=feb_data["weather_watcher"]["pest_alerts"],
            high_risk_crops=feb_data["weather_watcher"]["high_risk_crops"]
        ),
        soil_health=SoilHealthInput(
            soil_type=SoilType(feb_data["soil_health"]["soil_type"]),
            fertility=FertilityLevel(feb_data["soil_health"]["fertility"]),
            ph_level=feb_data["soil_health"]["ph_level"],
            organic_matter=feb_data["soil_health"]["organic_matter"],
            water_holding_capacity=feb_data["soil_health"]["water_holding_capacity"]
        ),
        irrigation_planner=IrrigationInput(
            water_availability=WaterAvailability(feb_data["irrigation_planner"]["water_availability"]),
            irrigation_reliability=IrrigationReliability(feb_data["irrigation_planner"]["irrigation_reliability"]),
            groundwater_level=feb_data["irrigation_planner"]["groundwater_level"],
            canal_supply=feb_data["irrigation_planner"]["canal_supply"]
        ),
        fertilizer_agent=FertilizerInput(
            nutrient_status=feb_data["fertilizer_agent"]["nutrient_status"],
            recommended_npk=feb_data["fertilizer_agent"]["recommended_npk"],
            soil_fertility_index=feb_data["fertilizer_agent"]["soil_fertility_index"],
            organic_matter_required=feb_data["fertilizer_agent"]["organic_matter_required"]
        ),
        market_intelligence=MarketInput(
            price_trend=MarketTrend(feb_data["market_intelligence"]["price_trend"]),
            market_volatility=MarketVolatility(feb_data["market_intelligence"]["market_volatility"]),
            demand_forecast=feb_data["market_intelligence"]["demand_forecast"],
            msp_supported_crops=feb_data["market_intelligence"]["msp_supported_crops"],
            insurance_supported_crops=feb_data["market_intelligence"]["insurance_supported_crops"],
            subsidy_favored_crops=feb_data["market_intelligence"]["subsidy_favored_crops"],
            price_stability=feb_data["market_intelligence"]["price_stability"]
        )
    )


def validate_agent_input(agent_name: str, agent_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate input for specific agent
    
    Args:
        agent_name: Name of the agent
        agent_data: Data from the agent
        required_fields: List of required fields for this agent
        
    Returns:
        Validation result
    """
    
    # Check required fields
    missing_required = [field for field in required_fields if field not in agent_data]
    if missing_required:
        return {
            "valid": False,
            "error": f"Missing required fields: {missing_required}",
            "required_fields": required_fields
        }
    
    return {
        "valid": True,
        "message": f"Agent {agent_name} input is valid",
        "required_fields": required_fields
    }


def get_supported_crops() -> List[str]:
    """Get list of all supported crops"""
    from agents.crop_requirements import get_all_crops
    return get_all_crops()


def get_seasonal_crops(season: str) -> List[str]:
    """Get crops suitable for a specific season"""
    from agents.crop_requirements import get_seasonal_crops
    return get_seasonal_crops(season)


def get_crop_requirements(crop: str) -> Dict[str, Any]:
    """Get requirements for a specific crop"""
    from agents.crop_requirements import get_crop_requirements
    return get_crop_requirements(crop)
