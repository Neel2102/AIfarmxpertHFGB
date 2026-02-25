"""
JSON Crop Selector - Takes inputs from existing agents and provides crop recommendations
Integrates with: weather watcher, irrigation planner, fertilizer, market intelligence, soil health agents
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .crop_selector_agent import CropSelectorAgent, FarmerContext


@dataclass
class AgentInputs:
    """JSON inputs from all specialized agents"""
    
    # Weather Watcher Agent Input
    weather: Dict[str, Any] = None
    
    # Irrigation Planner Agent Input  
    irrigation: Dict[str, Any] = None
    
    # Fertilizer Agent Input
    fertilizer: Dict[str, Any] = None
    
    # Market Intelligence Agent Input
    market: Dict[str, Any] = None
    
    # Soil Health Agent Input
    soil_health: Dict[str, Any] = None
    
    # Farmer Context
    farmer_context: Dict[str, Any] = None


class JSONCropSelector:
    """Crop selector that integrates JSON inputs from multiple agents"""
    
    def __init__(self):
        self.crop_selector = CropSelectorAgent()
    
    def select_crop_from_json(self, agent_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON inputs from all agents and return crop recommendation
        
        Args:
            agent_inputs: JSON object containing inputs from all agents
            
        Returns:
            Dict with crop recommendation and reasoning
        """
        
        # Parse agent inputs
        inputs = self._parse_agent_inputs(agent_inputs)
        
        # Convert to internal format
        farmer_context = self._convert_farmer_context(inputs.farmer_context)
        weather_data = self._convert_weather_data(inputs.weather)
        soil_data = self._convert_soil_data(inputs.soil_health)
        water_data = self._convert_water_data(inputs.irrigation)
        pest_data = self._convert_pest_data(inputs.weather)  # From weather agent
        market_data = self._convert_market_data(inputs.market)
        government_data = self._convert_government_data(inputs.market)  # From market agent
        
        # Get crop recommendation
        response = self.crop_selector.select_crops(
            farmer_context,
            weather_data,
            soil_data,
            water_data,
            pest_data,
            market_data,
            government_data
        )
        
        # Format output
        recommendation = self._format_json_output(response, inputs)
        
        return recommendation
    
    def _parse_agent_inputs(self, agent_inputs: Dict[str, Any]) -> AgentInputs:
        """Parse and validate agent inputs"""
        
        inputs = AgentInputs()
        
        # Weather Watcher Agent
        inputs.weather = agent_inputs.get('weather_watcher', {})
        
        # Irrigation Planner Agent
        inputs.irrigation = agent_inputs.get('irrigation_planner', {})
        
        # Fertilizer Agent
        inputs.fertilizer = agent_inputs.get('fertilizer_agent', {})
        
        # Market Intelligence Agent
        inputs.market = agent_inputs.get('market_intelligence', {})
        
        # Soil Health Agent
        inputs.soil_health = agent_inputs.get('soil_health', {})
        
        # Farmer Context
        inputs.farmer_context = agent_inputs.get('farmer_context', {})
        
        return inputs
    
    def _convert_farmer_context(self, farmer_data: Dict[str, Any]) -> FarmerContext:
        """Convert farmer context to internal format"""
        
        return FarmerContext(
            location=farmer_data.get('location', {"state": "", "district": ""}),
            season=farmer_data.get('season', 'Kharif'),
            land_size_acre=float(farmer_data.get('land_size_acre', 1.0)),
            risk_preference=farmer_data.get('risk_preference', 'Medium')
        )
    
    def _convert_weather_data(self, weather_data: Dict[str, Any]) -> 'WeatherOutput':
        """Convert weather agent data to internal format"""
        
        from .crop_selector_agent import WeatherOutput
        
        return WeatherOutput(
            monsoon_onset=weather_data.get('monsoon_onset', 'Normal'),
            rainfall_outlook=weather_data.get('rainfall_outlook', 'Normal'),
            dry_spell_risk=weather_data.get('dry_spell_risk', 'Medium'),
            heat_stress_risk=weather_data.get('heat_stress_risk', 'Medium')
        )
    
    def _convert_soil_data(self, soil_data: Dict[str, Any]) -> 'SoilOutput':
        """Convert soil health agent data to internal format"""
        
        from .crop_selector_agent import SoilOutput
        
        return SoilOutput(
            soil_type=soil_data.get('soil_type', 'Loamy'),
            fertility=soil_data.get('fertility', 'Medium'),
            water_holding=soil_data.get('water_holding_capacity', 'Medium')
        )
    
    def _convert_water_data(self, irrigation_data: Dict[str, Any]) -> 'WaterOutput':
        """Convert irrigation planner data to internal format"""
        
        from .crop_selector_agent import WaterOutput
        
        water_availability = irrigation_data.get('water_availability', 'Medium')
        if irrigation_data.get('irrigation_reliability'):
            irrigation_reliability = irrigation_data['irrigation_reliability']
        else:
            # Map water availability to irrigation reliability
            reliability_map = {'High': 'Good', 'Medium': 'Moderate', 'Low': 'Poor'}
            irrigation_reliability = reliability_map.get(water_availability, 'Moderate')
        
        return WaterOutput(
            water_availability=water_availability,
            irrigation_reliability=irrigation_reliability
        )
    
    def _convert_pest_data(self, weather_data: Dict[str, Any]) -> 'PestOutput':
        """Convert pest data (from weather agent) to internal format"""
        
        from .crop_selector_agent import PestOutput
        
        # Extract pest information from weather agent or use defaults
        pest_pressure = weather_data.get('pest_pressure', 'Medium')
        high_risk_crops = weather_data.get('high_risk_crops', [])
        alerts = weather_data.get('pest_alerts', [])
        
        return PestOutput(
            regional_pest_pressure=pest_pressure,
            high_risk_crops=high_risk_crops,
            alerts=alerts
        )
    
    def _convert_market_data(self, market_data: Dict[str, Any]) -> 'MarketOutput':
        """Convert market intelligence data to internal format"""
        
        from .crop_selector_agent import MarketOutput
        
        price_stability = market_data.get('price_stability', {})
        msp_crops = market_data.get('msp_supported_crops', [])
        volatility = market_data.get('market_volatility', 'Medium')
        
        return MarketOutput(
            price_stability=price_stability,
            msp_supported_crops=msp_crops,
            volatility_risk=volatility
        )
    
    def _convert_government_data(self, market_data: Dict[str, Any]) -> 'GovernmentOutput':
        """Convert government scheme data (from market agent) to internal format"""
        
        from .crop_selector_agent import GovernmentOutput
        
        insurance_crops = market_data.get('insurance_supported_crops', [])
        subsidy_crops = market_data.get('subsidy_favored_crops', [])
        
        return GovernmentOutput(
            insurance_supported_crops=insurance_crops,
            subsidy_favored_crops=subsidy_crops
        )
    
    def _format_json_output(self, response: Dict[str, Any], inputs: AgentInputs) -> Dict[str, Any]:
        """Format output as JSON response"""
        
        # Get top recommendation
        top_crop = None
        if response['recommendations']['safest']:
            top_crop = response['recommendations']['safest'][0]
        elif response['recommendations']['balanced']:
            top_crop = response['recommendations']['balanced'][0]
        
        # Build comprehensive JSON response
        output = {
            "recommendation": {
                "crop": top_crop['crop'] if top_crop else None,
                "confidence": response['confidence'],
                "risk_level": response['season_risk']['level'],
                "score": top_crop.get('score', 0) if top_crop else 0,
                "category": top_crop.get('category', 'unknown') if top_crop else 'unknown'
            },
            
            "agent_inputs_summary": {
                "weather": {
                    "rainfall_outlook": inputs.weather.get('rainfall_outlook', 'Unknown'),
                    "temperature_trend": inputs.weather.get('temperature_trend', 'Unknown'),
                    "pest_pressure": inputs.weather.get('pest_pressure', 'Unknown')
                },
                "soil_health": {
                    "soil_type": inputs.soil_health.get('soil_type', 'Unknown'),
                    "fertility": inputs.soil_health.get('fertility', 'Unknown'),
                    "ph_level": inputs.soil_health.get('ph_level', 'Unknown'),
                    "organic_matter": inputs.soil_health.get('organic_matter', 'Unknown')
                },
                "irrigation": {
                    "water_availability": inputs.irrigation.get('water_availability', 'Unknown'),
                    "irrigation_reliability": inputs.irrigation.get('irrigation_reliability', 'Unknown'),
                    "groundwater_level": inputs.irrigation.get('groundwater_level', 'Unknown')
                },
                "fertilizer": {
                    "nutrient_status": inputs.fertilizer.get('nutrient_status', 'Unknown'),
                    "recommended_npk": inputs.fertilizer.get('recommended_npk', 'Unknown'),
                    "soil_fertility_index": inputs.fertilizer.get('soil_fertility_index', 'Unknown')
                },
                "market": {
                    "price_trend": inputs.market.get('price_trend', 'Unknown'),
                    "market_volatility": inputs.market.get('market_volatility', 'Unknown'),
                    "demand_forecast": inputs.market.get('demand_forecast', 'Unknown'),
                    "msp_support": inputs.market.get('msp_supported_crops', [])
                }
            },
            
            "detailed_reasoning": {
                "weather_impact": self._explain_weather_impact(top_crop, inputs.weather) if top_crop else "No crop selected",
                "soil_impact": self._explain_soil_impact(top_crop, inputs.soil_health) if top_crop else "No crop selected",
                "water_impact": self._explain_water_impact(top_crop, inputs.irrigation) if top_crop else "No crop selected",
                "market_impact": self._explain_market_impact(top_crop, inputs.market) if top_crop else "No crop selected",
                "fertilizer_impact": self._explain_fertilizer_impact(top_crop, inputs.fertilizer) if top_crop else "No crop selected"
            },
            
            "all_recommendations": {
                "safest": response['recommendations']['safest'],
                "balanced": response['recommendations']['balanced'],
                "higher_risk": response['recommendations']['higher_risk'],
                "avoid": response['avoid']
            },
            
            "practical_guidance": {
                "sowing_window": self._get_sowing_window(inputs.farmer_context.get('season', 'Kharif'), top_crop['crop']) if top_crop else "Unknown",
                "seed_requirements": self._get_seed_requirements(inputs.farmer_context.get('land_size_acre', 1.0), top_crop['crop']) if top_crop else "Unknown",
                "land_preparation": self._get_land_preparation(inputs.soil_health.get('soil_type', 'Loamy')),
                "irrigation_schedule": self._get_irrigation_schedule(top_crop['crop'], inputs.irrigation) if top_crop else "Unknown",
                "fertilizer_recommendation": inputs.fertilizer.get('recommended_npk', 'Standard NPK'),
                "expected_challenges": self._get_expected_challenges(inputs)
            },
            
            "next_steps": [
                f"Book quality {top_crop['crop']} seeds from authorized dealer" if top_crop else "Select appropriate crop seeds",
                f"Prepare land according to {inputs.soil_health.get('soil_type', 'soil')} requirements",
                f"Arrange irrigation (availability: {inputs.irrigation.get('water_availability', 'unknown')})",
                "Apply recommended fertilizers as per soil test",
                "Monitor weather forecasts regularly",
                "Contact local agriculture office for scheme benefits"
            ],
            
            "metadata": {
                "farmer_location": inputs.farmer_context.get('location', {}),
                "season": inputs.farmer_context.get('season', 'Unknown'),
                "land_size_acre": inputs.farmer_context.get('land_size_acre', 0),
                "risk_preference": inputs.farmer_context.get('risk_preference', 'Medium'),
                "processing_timestamp": "2026-02-06T21:52:00Z",
                "model_version": "v1.0"
            }
        }
        
        return output
    
    def _explain_weather_impact(self, crop: Dict, weather_data: Dict) -> str:
        """Explain weather impact on crop selection"""
        rainfall = weather_data.get('rainfall_outlook', 'Normal')
        temperature = weather_data.get('temperature_trend', 'Normal')
        
        return f"Current {rainfall} rainfall and {temperature} temperature conditions favor {crop['crop']} cultivation"
    
    def _explain_soil_impact(self, crop: Dict, soil_data: Dict) -> str:
        """Explain soil impact on crop selection"""
        soil_type = soil_data.get('soil_type', 'Loamy')
        fertility = soil_data.get('fertility', 'Medium')
        ph = soil_data.get('ph_level', 'Neutral')
        
        return f"{soil_type} soil with {fertility} fertility and {ph} pH provides ideal conditions for {crop['crop']}"
    
    def _explain_water_impact(self, crop: Dict, irrigation_data: Dict) -> str:
        """Explain water impact on crop selection"""
        water_avail = irrigation_data.get('water_availability', 'Medium')
        reliability = irrigation_data.get('irrigation_reliability', 'Moderate')
        
        return f"Water availability is {water_avail} with {reliability} irrigation reliability, suitable for {crop['crop']}"
    
    def _explain_market_impact(self, crop: Dict, market_data: Dict) -> str:
        """Explain market impact on crop selection"""
        price_trend = market_data.get('price_trend', 'Stable')
        msp_crops = market_data.get('msp_supported_crops', [])
        
        msp_status = "MSP support available" if crop['crop'] in msp_crops else "No MSP support"
        return f"Market trend is {price_trend} with {msp_status} for {crop['crop']}"
    
    def _explain_fertilizer_impact(self, crop: Dict, fertilizer_data: Dict) -> str:
        """Explain fertilizer impact on crop selection"""
        nutrient_status = fertilizer_data.get('nutrient_status', 'Balanced')
        npk = fertilizer_data.get('recommended_npk', 'Standard')
        
        return f"Soil nutrient status is {nutrient_status} with {npk} fertilizer recommendation for {crop['crop']}"
    
    def _get_sowing_window(self, season: str, crop: str) -> str:
        """Get sowing window for crop and season"""
        windows = {
            ("Kharif", "Rice"): "June-July with monsoon onset",
            ("Kharif", "Cotton"): "April-May pre-monsoon",
            ("Kharif", "Maize"): "June-July early monsoon",
            ("Rabi", "Wheat"): "October-November post-monsoon",
            ("Rabi", "Mustard"): "October-November cool season",
            ("Rabi", "Chickpea"): "October-November winter",
            ("Zaid", "Cucumber"): "February-March summer",
            ("Zaid", "Watermelon"): "February-March warm season"
        }
        return windows.get((season, crop), f"Standard {season.lower()} sowing period")
    
    def _get_seed_requirements(self, acres: float, crop: str) -> str:
        """Get seed requirements"""
        rates = {
            "Rice": "25-30 kg/acre",
            "Wheat": "40-50 kg/acre",
            "Cotton": "1.5-2 kg/acre",
            "Maize": "8-10 kg/acre",
            "Groundnut": "80-100 kg/acre",
            "Mustard": "2-3 kg/acre",
            "Chickpea": "60-80 kg/acre",
            "Sorghum": "8-10 kg/acre"
        }
        rate = rates.get(crop, "Standard rate")
        return f"{rate} (Total: {rate} for {acres} acres)"
    
    def _get_land_preparation(self, soil_type: str) -> str:
        """Get land preparation recommendations"""
        preps = {
            "Clay": "Deep plowing + 2-3 harrowings + leveling for water retention",
            "Loamy": "1-2 plowings + harrowing + fine tilth preparation",
            "Sandy": "Light plowing + organic matter + moisture conservation"
        }
        return preps.get(soil_type, "Standard preparation with proper leveling")
    
    def _get_irrigation_schedule(self, crop: str, irrigation_data: Dict) -> str:
        """Get irrigation schedule"""
        schedules = {
            "Rice": "Continuous flooding or alternate wetting-drying (5-7 cm depth)",
            "Wheat": "4-5 irrigations at critical growth stages",
            "Cotton": "At flowering, boll development, and boll opening",
            "Maize": "At knee-high, tasseling, and grain filling stages",
            "Groundnut": "At flowering and pod development stages"
        }
        base = schedules.get(crop, "As per crop growth stages")
        water_avail = irrigation_data.get('water_availability', 'Medium')
        return f"{base} (Current availability: {water_avail})"
    
    def _get_expected_challenges(self, inputs: AgentInputs) -> List[str]:
        """Get expected challenges based on agent inputs"""
        challenges = []
        
        # Weather challenges
        if inputs.weather.get('dry_spell_risk') == 'High':
            challenges.append("Dry spells may affect germination")
        
        # Water challenges
        if inputs.irrigation.get('water_availability') == 'Low':
            challenges.append("Water scarcity - consider drought-resistant varieties")
        
        # Pest challenges
        if inputs.weather.get('pest_pressure') == 'High':
            challenges.append("High pest pressure - prepare integrated pest management")
        
        # Market challenges
        if inputs.market.get('market_volatility') == 'High':
            challenges.append("Market price volatility - consider forward contracts")
        
        # Soil challenges
        if inputs.soil_health.get('fertility') == 'Low':
            challenges.append("Low soil fertility - increase organic matter and fertilizers")
        
        return challenges if challenges else ["Monitor weather forecasts regularly", "Maintain proper field records"]


def main():
    """Demonstrate JSON crop selector with sample agent inputs"""
    
    selector = JSONCropSelector()
    
    # Sample JSON inputs from all agents
    sample_inputs = {
        "farmer_context": {
            "location": {"state": "Punjab", "district": "Ludhiana"},
            "season": "Kharif",
            "land_size_acre": 5.0,
            "risk_preference": "Low"
        },
        
        "weather_watcher": {
            "rainfall_outlook": "Normal",
            "temperature_trend": "Normal",
            "monsoon_onset": "Normal",
            "dry_spell_risk": "Low",
            "heat_stress_risk": "Low",
            "pest_pressure": "Medium",
            "pest_alerts": ["Bollworm expected in cotton", "Leaf miner in groundnut"],
            "high_risk_crops": ["Cotton", "Groundnut", "Pigeon Pea"]
        },
        
        "soil_health": {
            "soil_type": "Loamy",
            "fertility": "Medium",
            "ph_level": "Neutral",
            "organic_matter": "Medium",
            "water_holding_capacity": "Medium"
        },
        
        "irrigation_planner": {
            "water_availability": "High",
            "irrigation_reliability": "Good",
            "groundwater_level": "Normal",
            "canal_supply": "Adequate"
        },
        
        "fertilizer_agent": {
            "nutrient_status": "Balanced",
            "recommended_npk": "NPK 20-20-20",
            "soil_fertility_index": "Medium",
            "organic_matter_required": "Medium"
        },
        
        "market_intelligence": {
            "price_trend": "Stable",
            "market_volatility": "Medium",
            "demand_forecast": "Stable",
            "msp_supported_crops": ["Rice", "Wheat", "Cotton", "Groundnut"],
            "insurance_supported_crops": ["Rice", "Wheat", "Cotton", "Groundnut"],
            "subsidy_favored_crops": ["Rice", "Wheat", "Cotton"],
            "price_stability": {
                "Rice": "High",
                "Wheat": "High",
                "Cotton": "Medium"
            }
        }
    }
    
    # Get crop recommendation
    recommendation = selector.select_crop_from_json(sample_inputs)
    
    # Print JSON output
    print("JSON CROP SELECTOR OUTPUT")
    print("=" * 50)
    print(json.dumps(recommendation, indent=2))


if __name__ == "__main__":
    main()
