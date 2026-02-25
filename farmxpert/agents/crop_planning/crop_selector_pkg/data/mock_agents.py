"""
Mock specialized agents for testing the Crop Selector Agent
"""

import random
from typing import Dict, List
from ..agents.crop_selector_agent import WeatherOutput, SoilOutput, WaterOutput, PestOutput, MarketOutput, GovernmentOutput


class WeatherAgent:
    """Mock weather agent that simulates weather predictions"""
    
    def __init__(self):
        self.regions = {
            "Punjab": {"monsoon": "Normal", "rainfall": "Normal", "dry_spell": "Low", "heat": "Low"},
            "Maharashtra": {"monsoon": "Delayed", "rainfall": "Below", "dry_spell": "High", "heat": "High"},
            "Tamil Nadu": {"monsoon": "Normal", "rainfall": "Normal", "dry_spell": "Medium", "heat": "Medium"},
            "Uttar Pradesh": {"monsoon": "Early", "rainfall": "Above", "dry_spell": "Low", "heat": "Medium"},
            "Rajasthan": {"monsoon": "Delayed", "rainfall": "Below", "dry_spell": "High", "heat": "High"},
            "West Bengal": {"monsoon": "Normal", "rainfall": "Above", "dry_spell": "Low", "heat": "Low"},
            "Karnataka": {"monsoon": "Normal", "rainfall": "Normal", "dry_spell": "Medium", "heat": "Medium"},
            "Gujarat": {"monsoon": "Delayed", "rainfall": "Below", "dry_spell": "High", "heat": "High"}
        }
    
    def get_weather_forecast(self, state: str, season: str) -> WeatherOutput:
        """Get weather forecast for a given state and season"""
        base_weather = self.regions.get(state, self.regions["Punjab"])
        
        # Add some randomness for realism
        rainfall_options = ["Below", "Normal", "Above"]
        if base_weather["rainfall"] == "Below":
            rainfall_options = ["Below", "Normal"]
        elif base_weather["rainfall"] == "Above":
            rainfall_options = ["Normal", "Above"]
        
        return WeatherOutput(
            monsoon_onset=base_weather["monsoon"],
            rainfall_outlook=random.choice(rainfall_options),
            dry_spell_risk=base_weather["dry_spell"],
            heat_stress_risk=base_weather["heat"]
        )


class SoilAgent:
    """Mock soil agent that simulates soil analysis"""
    
    def __init__(self):
        self.soil_data = {
            "Punjab": {"type": "Loamy", "fertility": "High", "water_holding": "Medium"},
            "Maharashtra": {"type": "Sandy", "fertility": "Low", "water_holding": "Low"},
            "Tamil Nadu": {"type": "Clay", "fertility": "Medium", "water_holding": "High"},
            "Uttar Pradesh": {"type": "Loamy", "fertility": "High", "water_holding": "Medium"},
            "Rajasthan": {"type": "Sandy", "fertility": "Low", "water_holding": "Low"},
            "West Bengal": {"type": "Clay", "fertility": "High", "water_holding": "High"},
            "Karnataka": {"type": "Loamy", "fertility": "Medium", "water_holding": "Medium"},
            "Gujarat": {"type": "Sandy", "fertility": "Medium", "water_holding": "Low"}
        }
    
    def get_soil_analysis(self, state: str, district: str) -> SoilOutput:
        """Get soil analysis for a given location"""
        base_soil = self.soil_data.get(state, self.soil_data["Punjab"])
        
        # Add some district-level variation
        fertility_options = ["Low", "Medium", "High"]
        if base_soil["fertility"] == "Low":
            fertility_options = ["Low", "Medium"]
        elif base_soil["fertility"] == "High":
            fertility_options = ["Medium", "High"]
        
        return SoilOutput(
            soil_type=base_soil["type"],
            fertility=random.choice(fertility_options),
            water_holding=base_soil["water_holding"]
        )


class WaterAgent:
    """Mock water/groundwater agent that simulates water availability"""
    
    def __init__(self):
        self.water_data = {
            "Punjab": {"availability": "High", "irrigation": "Good"},
            "Maharashtra": {"availability": "Low", "irrigation": "Poor"},
            "Tamil Nadu": {"availability": "Medium", "irrigation": "Moderate"},
            "Uttar Pradesh": {"availability": "High", "irrigation": "Good"},
            "Rajasthan": {"availability": "Low", "irrigation": "Poor"},
            "West Bengal": {"availability": "High", "irrigation": "Good"},
            "Karnataka": {"availability": "Medium", "irrigation": "Moderate"},
            "Gujarat": {"availability": "Low", "irrigation": "Poor"}
        }
    
    def get_water_availability(self, state: str, season: str) -> WaterOutput:
        """Get water availability for a given state and season"""
        base_water = self.water_data.get(state, self.water_data["Punjab"])
        
        # Seasonal variations
        if season == "Kharif" and base_water["availability"] == "Low":
            # Kharif season might have slightly better water due to monsoon
            availability = "Medium" if random.random() > 0.5 else "Low"
        else:
            availability = base_water["availability"]
        
        return WaterOutput(
            water_availability=availability,
            irrigation_reliability=base_water["irrigation"]
        )


class PestAgent:
    """Mock pest & disease agent that simulates pest pressure"""
    
    def __init__(self):
        self.pest_data = {
            "Kharif": {
                "pressure": "High",
                "high_risk_crops": ["Cotton", "Groundnut", "Pigeon Pea"],
                "alerts": ["Bollworm expected in cotton", "Leaf miner in groundnut"]
            },
            "Rabi": {
                "pressure": "Medium",
                "high_risk_crops": ["Wheat", "Mustard", "Chickpea"],
                "alerts": ["Aphids expected in mustard", "Rust in wheat"]
            },
            "Zaid": {
                "pressure": "Low",
                "high_risk_crops": ["Cucumber", "Watermelon"],
                "alerts": ["Fruit fly risk in cucurbits"]
            }
        }
    
    def get_pest_analysis(self, state: str, season: str) -> PestOutput:
        """Get pest analysis for a given state and season"""
        base_pest = self.pest_data.get(season, self.pest_data["Kharif"])
        
        # State-specific variations
        pressure_variations = {
            "West Bengal": "High",  # High humidity
            "Rajasthan": "Low",     # Dry climate
            "Kerala": "High",       # High humidity
            "Punjab": "Medium"
        }
        
        pressure = pressure_variations.get(state, base_pest["pressure"])
        
        return PestOutput(
            regional_pest_pressure=pressure,
            high_risk_crops=base_pest["high_risk_crops"],
            alerts=base_pest["alerts"]
        )


class MarketAgent:
    """Mock market agent that simulates market conditions"""
    
    def __init__(self):
        self.msp_crops = [
            "Rice", "Wheat", "Cotton", "Groundnut", "Mustard",
            "Chickpea", "Pigeon Pea", "Green Gram", "Black Gram"
        ]
        
        self.price_stability = {
            "Rice": "High", "Wheat": "High", "Cotton": "Medium",
            "Groundnut": "Medium", "Mustard": "Medium", "Chickpea": "High",
            "Pigeon Pea": "Medium", "Green Gram": "Medium", "Black Gram": "Medium",
            "Maize": "Medium", "Soybean": "Medium", "Barley": "Low",
            "Lentil": "Medium", "Pea": "Low", "Potato": "Low", "Onion": "Low"
        }
    
    def get_market_analysis(self, state: str, season: str) -> MarketOutput:
        """Get market analysis for a given state and season"""
        
        # Filter MSP crops by season
        season_msp = {
            "Kharif": ["Rice", "Cotton", "Groundnut", "Pigeon Pea", "Green Gram", "Black Gram"],
            "Rabi": ["Wheat", "Mustard", "Chickpea"],
            "Zaid": []  # No major MSP crops in Zaid
        }
        
        msp_supported = season_msp.get(season, [])
        
        # Market volatility by season
        volatility = {"Kharif": "Medium", "Rabi": "Low", "Zaid": "High"}.get(season, "Medium")
        
        return MarketOutput(
            price_stability=self.price_stability,
            msp_supported_crops=msp_supported,
            volatility_risk=volatility
        )


class GovernmentAgent:
    """Mock government scheme agent that simulates policy support"""
    
    def __init__(self):
        self.insurance_crops = [
            "Rice", "Wheat", "Cotton", "Groundnut", "Mustard",
            "Chickpea", "Pigeon Pea", "Maize", "Soybean"
        ]
        
        self.subsidy_crops = [
            "Rice", "Wheat", "Cotton", "Groundnut", "Mustard"
        ]
    
    def get_scheme_analysis(self, state: str, season: str) -> GovernmentOutput:
        """Get government scheme analysis"""
        
        # Filter by season
        season_insurance = {
            "Kharif": ["Rice", "Cotton", "Groundnut", "Pigeon Pea", "Maize"],
            "Rabi": ["Wheat", "Mustard", "Chickpea"],
            "Zaid": []  # Limited insurance in Zaid
        }
        
        season_subsidy = {
            "Kharif": ["Rice", "Cotton", "Groundnut"],
            "Rabi": ["Wheat", "Mustard"],
            "Zaid": []
        }
        
        return GovernmentOutput(
            insurance_supported_crops=season_insurance.get(season, []),
            subsidy_favored_crops=season_subsidy.get(season, [])
        )


class MockAgentOrchestrator:
    """Orchestrator that manages all mock agents"""
    
    def __init__(self):
        self.weather_agent = WeatherAgent()
        self.soil_agent = SoilAgent()
        self.water_agent = WaterAgent()
        self.pest_agent = PestAgent()
        self.market_agent = MarketAgent()
        self.government_agent = GovernmentAgent()
    
    def get_all_agent_outputs(self, state: str, district: str, season: str) -> Dict:
        """Get outputs from all specialized agents"""
        return {
            "weather": self.weather_agent.get_weather_forecast(state, season),
            "soil": self.soil_agent.get_soil_analysis(state, district),
            "water": self.water_agent.get_water_availability(state, season),
            "pest": self.pest_agent.get_pest_analysis(state, season),
            "market": self.market_agent.get_market_analysis(state, season),
            "government": self.government_agent.get_scheme_analysis(state, season)
        }
