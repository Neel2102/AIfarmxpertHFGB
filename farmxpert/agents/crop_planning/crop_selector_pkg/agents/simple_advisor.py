"""
Simple Crop Advisor - Simple, medium-length output with February 2026 real data
"""

from .human_crop_advisor import HumanCropAdvisor
from ..data.february_data import get_february_data


class SimpleAdvisor:
    """Simple crop advisor with medium-length output"""
    
    def __init__(self):
        self.advisor = HumanCropAdvisor()
    
    def get_simple_recommendation(self, state: str, district: str, acres: float = 5.0, risk: str = "Medium") -> str:
        """Get simple, medium-length crop recommendation"""
        
        # Get February data
        agent_data = get_february_data(state)
        
        # Add farmer context
        inputs = {
            "farmer_context": {
                "location": {"state": state, "district": district},
                "season": "Rabi",
                "land_size_acre": acres,
                "risk_preference": risk
            },
            **agent_data
        }
        
        # Get recommendation
        json_rec = self.advisor.json_selector.select_crop_from_json(inputs)
        
        # Format simple output
        crop = json_rec['recommendation']['crop']
        confidence = json_rec['recommendation']['confidence']
        score = json_rec['recommendation']['score']
        
        # Extract key info
        weather = agent_data['weather_watcher']
        soil = agent_data['soil_health']
        water = agent_data['irrigation_planner']
        market = agent_data['market_intelligence']
        
        output = f"""
CROP RECOMMENDATION FOR {district.upper()}, {state.upper()}
================================================

RECOMMENDED CROP: {crop.upper()}
- Confidence: {confidence}
- Match Score: {score:.1%}
- Risk Level: {json_rec['recommendation']['risk_level']}

CURRENT CONDITIONS (February 2026):
Weather: {weather['rainfall_outlook']} rainfall, {weather['temperature_trend']} temperatures
Soil: {soil['soil_type']} soil with {soil['fertility']} fertility
Water: {water['water_availability']} availability, {water['irrigation_reliability']} irrigation
Market: {market['price_trend']} prices, {'MSP support' if crop in market['msp_supported_crops'] else 'No MSP'}

WHY {crop.upper()} IS BEST:
- Weather: {weather['rainfall_outlook']} rainfall and {weather['temperature_trend']} temps favor {crop.lower()}
- Soil: {soil['soil_type']} soil provides ideal growing conditions
- Water: {water['water_availability']} water availability suits crop needs
- Market: {market['price_trend']} prices with {'government support' if crop in market['msp_supported_crops'] else 'good demand'}

PRACTICAL GUIDANCE:
- Sowing: October-November (Rabi season)
- Seeds: {self._get_seed_rate(acres, crop)}
- Fertilizer: {agent_data['fertilizer_agent']['recommended_npk']}
- Irrigation: {self._get_irrigation_needs(crop, water)}

EXPECTED CHALLENGES:
{self._get_challenges(weather, soil, water, market)}

NEXT STEPS:
1. Book quality {crop} seeds from authorized dealer
2. Prepare land for {soil['soil_type'].lower()} soil
3. Arrange irrigation (current: {water['water_availability']})
4. Apply {agent_data['fertilizer_agent']['recommended_npk']} fertilizer
5. Monitor weather and pest alerts

BOTTOM LINE: {crop.upper()} is your best choice for {acres} acres in {district} this season with {score:.1%} match to current conditions.
        """.strip()
        
        return output
    
    def _get_seed_rate(self, acres: float, crop: str) -> str:
        """Get seed requirements"""
        rates = {
            "Wheat": "40-50 kg/acre",
            "Mustard": "2-3 kg/acre",
            "Chickpea": "60-80 kg/acre",
            "Cumin": "8-10 kg/acre",
            "Cotton": "1.5-2 kg/acre",
            "Groundnut": "80-100 kg/acre"
        }
        rate = rates.get(crop, "Standard rate")
        return f"{rate} (Total: {rate} for {acres} acres)"
    
    def _get_irrigation_needs(self, crop: str, water_data: dict) -> str:
        """Get irrigation needs"""
        needs = {
            "Wheat": "4-5 irrigations at critical stages",
            "Mustard": "2-3 irrigations at flowering and pod filling",
            "Chickpea": "2-3 irrigations at flowering and pod development",
            "Cumin": "Drip irrigation recommended",
            "Cotton": "Irrigation at flowering and boll development",
            "Groundnut": "Irrigation at flowering and pod development"
        }
        base = needs.get(crop, "As per crop requirements")
        return f"{base} (Current: {water_data['water_availability']} availability)"
    
    def _get_challenges(self, weather: dict, soil: dict, water: dict, market: dict) -> str:
        """Get expected challenges"""
        challenges = []
        
        if weather['dry_spell_risk'] == 'High':
            challenges.append("- Dry spells may affect germination")
        if water['water_availability'] == 'Low':
            challenges.append("- Water scarcity - choose drought varieties")
        if soil['fertility'] == 'Low':
            challenges.append("- Low soil fertility - add organic matter")
        if market['market_volatility'] == 'High':
            challenges.append("- Market volatility - consider forward contracts")
        
        if not challenges:
            challenges = ["- Monitor weather forecasts regularly", "- Maintain field records"]
        
        return '\n'.join(challenges[:3])  # Limit to 3 challenges


def main():
    """Demonstrate simple advisor with February 2026 data - single input case"""
    
    advisor = SimpleAdvisor()
    
    # Single input case - Punjab
    state = "Punjab"
    district = "Ludhiana"
    
    print(f"CROP ADVISOR - SINGLE INPUT CASE")
    print("=" * 50)
    print(f"Location: {district}, {state}")
    print(f"Season: Rabi (February 2026)")
    print("=" * 50)
    
    recommendation = advisor.get_simple_recommendation(state, district)
    print(recommendation)


if __name__ == "__main__":
    main()
