"""
Models package - Data models for crop advisor system
"""

# Input models
from .input import (
    Season,
    RiskLevel,
    RainfallOutlook,
    TemperatureTrend,
    WaterAvailability,
    IrrigationReliability,
    SoilType,
    FertilityLevel,
    MarketTrend,
    MarketVolatility,
    PestPressure,
    Location,
    FarmerContext,
    WeatherInput,
    SoilHealthInput,
    IrrigationInput,
    FertilizerInput,
    MarketInput,
    CropAdvisorInput
)

# Output models
from .output import (
    CropRecommendation,
    AgentInputsSummary,
    DetailedReasoning,
    PracticalGuidance,
    CropAdvisorOutput,
    SimpleRecommendation,
    HumanReadableRecommendation,
    JSONRecommendation,
    DetailedRecommendation,
    OutputFactory
)

# Validation and utilities
from .validation import validate_input, create_sample_input

__all__ = [
    # Input models
    'Season',
    'RiskLevel',
    'RainfallOutlook',
    'TemperatureTrend',
    'WaterAvailability',
    'IrrigationReliability',
    'SoilType',
    'FertilityLevel',
    'MarketTrend',
    'MarketVolatility',
    'PestPressure',
    'Location',
    'FarmerContext',
    'WeatherInput',
    'SoilHealthInput',
    'IrrigationInput',
    'FertilizerInput',
    'MarketInput',
    'CropAdvisorInput',
    
    # Output models
    'CropRecommendation',
    'AgentInputsSummary',
    'DetailedReasoning',
    'PracticalGuidance',
    'CropAdvisorOutput',
    'SimpleRecommendation',
    'HumanReadableRecommendation',
    'JSONRecommendation',
    'DetailedRecommendation',
    'OutputFactory',
    
    # Validation and utilities
    'validate_input',
    'create_sample_input'
]
