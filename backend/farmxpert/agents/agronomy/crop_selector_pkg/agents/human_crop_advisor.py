"""
Human Crop Advisor - Takes JSON inputs from agents and provides human-readable output with summary
"""

import json
from typing import Dict, List, Any
from .json_crop_selector import JSONCropSelector


class HumanCropAdvisor:
    """Converts agent JSON inputs to human-readable crop recommendations with summary"""
    
    def __init__(self):
        self.json_selector = JSONCropSelector()
    
    def get_human_recommendation(self, agent_inputs: Dict[str, Any]) -> str:
        """
        Convert agent JSON inputs to human-readable recommendation
        
        Args:
            agent_inputs: JSON object containing inputs from all agents
            
        Returns:
            Human-readable string with crop recommendation and summary
        """
        
        # Get JSON recommendation
        json_recommendation = self.json_selector.select_crop_from_json(agent_inputs)
        
        # Convert to human-readable format
        human_output = self._format_human_output(json_recommendation, agent_inputs)
        
        return human_output
    
    def _format_human_output(self, recommendation: Dict[str, Any], agent_inputs: Dict[str, Any]) -> str:
        """Format recommendation as human-readable text"""
        
        # Extract key information
        crop = recommendation['recommendation']['crop']
        confidence = recommendation['recommendation']['confidence']
        risk_level = recommendation['recommendation']['risk_level']
        score = recommendation['recommendation']['score']
        
        # Extract agent summaries
        weather = agent_inputs.get('weather_watcher', {})
        soil = agent_inputs.get('soil_health', {})
        irrigation = agent_inputs.get('irrigation_planner', {})
        fertilizer = agent_inputs.get('fertilizer_agent', {})
        market = agent_inputs.get('market_intelligence', {})
        farmer = agent_inputs.get('farmer_context', {})
        
        # Build human-readable output
        output = f"""
CROP RECOMMENDATION SUMMARY
===========================

RECOMMENDED CROP: {crop.upper()}

OVERALL ASSESSMENT:
- Confidence Level: {confidence}
- Risk Level: {risk_level}
- Match Score: {score:.1%}
- Best For: {farmer.get('land_size_acre', 1.0)} acres in {farmer.get('location', {}).get('district', 'your area')}

WHY THIS CROP IS RECOMMENDED:

Weather Conditions:
- Expected rainfall: {weather.get('rainfall_outlook', 'normal')}
- Temperature pattern: {weather.get('temperature_trend', 'normal')}
- Pest pressure: {weather.get('pest_pressure', 'moderate')}
- Impact: {recommendation['detailed_reasoning']['weather_impact']}

Soil Conditions:
- Soil type: {soil.get('soil_type', 'loamy')}
- Fertility level: {soil.get('fertility', 'medium')}
- pH level: {soil.get('ph_level', 'neutral')}
- Impact: {recommendation['detailed_reasoning']['soil_impact']}

Water Availability:
- Water supply: {irrigation.get('water_availability', 'medium')}
- Irrigation reliability: {irrigation.get('irrigation_reliability', 'moderate')}
- Impact: {recommendation['detailed_reasoning']['water_impact']}

Nutrient Status:
- Soil nutrients: {fertilizer.get('nutrient_status', 'balanced')}
- Recommended fertilizer: {fertilizer.get('recommended_npk', 'standard NPK')}
- Impact: {recommendation['detailed_reasoning']['fertilizer_impact']}

Market Conditions:
- Price trend: {market.get('price_trend', 'stable')}
- Market volatility: {market.get('market_volatility', 'medium')}
- Government support: {'MSP available' if crop in market.get('msp_supported_crops', []) else 'No MSP'}
- Impact: {recommendation['detailed_reasoning']['market_impact']}

PRACTICAL GUIDANCE:

Sowing Information:
- Best time to plant: {recommendation['practical_guidance']['sowing_window']}
- Seeds needed: {recommendation['practical_guidance']['seed_requirements']}
- Land preparation: {recommendation['practical_guidance']['land_preparation']}

Water Management:
- Irrigation schedule: {recommendation['practical_guidance']['irrigation_schedule']}
- Current water situation: {irrigation.get('water_availability', 'medium')} availability

Fertilizer Application:
- Recommended: {recommendation['practical_guidance']['fertilizer_recommendation']}
- Application timing: As per soil test recommendations

EXPECTED CHALLENGES:
"""
        
        # Add challenges
        challenges = recommendation['practical_guidance']['expected_challenges']
        for challenge in challenges:
            output += f"- {challenge}\n"
        
        output += f"""
ACTION PLAN:

Next Steps:
"""
        
        # Add action steps
        steps = recommendation['next_steps']
        for i, step in enumerate(steps, 1):
            output += f"{i}. {step}\n"
        
        # Add summary
        output += f"""
EXECUTIVE SUMMARY:
-----------------

Based on analysis from all specialized agents, {crop.upper()} is the best choice for your farm.

Key Reasons:
1. Weather patterns ({weather.get('rainfall_outlook', 'normal')} rainfall) are ideal for {crop}
2. Your {soil.get('soil_type', 'soil')} soil provides good growing conditions
3. Water availability ({irrigation.get('water_availability', 'medium')}) meets crop needs
4. Market conditions are {market.get('price_trend', 'stable')} with {'government price support' if crop in market.get('msp_supported_crops', []) else 'market-based pricing'}
5. Soil nutrients are {fertilizer.get('nutrient_status', 'adequate')} for optimal growth

Expected Outcome:
- High success probability due to {confidence.lower()} confidence level
- {risk_level.lower()} risk profile suitable for your {farmer.get('risk_preference', 'medium')} risk preference
- Good market prospects with stable demand

Bottom Line: Plant {crop.upper()} this season for the best balance of weather suitability, soil compatibility, water availability, and market stability.

Recommendation Confidence: {score:.1%} match with your farm conditions
        """.strip()
        
        return output
    
    def get_simple_summary(self, agent_inputs: Dict[str, Any]) -> str:
        """Get a simple one-paragraph summary"""
        
        # Get recommendation
        json_recommendation = self.json_selector.select_crop_from_json(agent_inputs)
        
        # Extract key info
        crop = json_recommendation['recommendation']['crop']
        confidence = json_recommendation['recommendation']['confidence']
        risk = json_recommendation['recommendation']['risk_level']
        
        farmer = agent_inputs.get('farmer_context', {})
        weather = agent_inputs.get('weather_watcher', {})
        soil = agent_inputs.get('soil_health', {})
        market = agent_inputs.get('market_intelligence', {})
        
        summary = f"""
Based on analysis from weather, soil, water, fertilizer, and market agents, we recommend planting {crop.upper()} 
for your {farmer.get('land_size_acre', 1.0)} acres in {farmer.get('location', {}).get('district', 'your area')} this {farmer.get('season', 'season')} season. 

This recommendation has {confidence.lower()} confidence with {risk.lower()} risk because: 
{weather.get('rainfall_outlook', 'normal')} rainfall patterns favor {crop}, your {soil.get('soil_type', 'soil')} soil provides ideal growing conditions, 
water availability is {agent_inputs.get('irrigation_planner', {}).get('water_availability', 'adequate')}, and market conditions are {market.get('price_trend', 'stable')} 
with {'government price support' if crop in market.get('msp_supported_crops', []) else 'good demand prospects'}.

The crop scores {json_recommendation['recommendation']['score']:.1%} match with your specific farm conditions and risk preference.
        """.strip()
        
        return summary


def main():
    """Demonstrate human-readable output with February 2026 real data"""
    
    advisor = HumanCropAdvisor()
    
    # February 2026 real data inputs from all agents
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.february_data import get_february_data
    
    # Test with different states
    states = ["Punjab", "Maharashtra", "Rajasthan", "Tamil Nadu"]
    
    for state in states:
        print(f"\n{'='*60}")
        print(f"{state.upper()} - FEBRUARY 2026 CROP RECOMMENDATION")
        print('='*60)
        
        # Get real February data
        agent_data = get_february_data(state)
        
        # Add farmer context
        sample_inputs = {
            "farmer_context": {
                "location": {"state": state, "district": f"Sample District"},
                "season": "Rabi",  # February is Rabi season
                "land_size_acre": 5.0,
                "risk_preference": "Medium"
            },
            **agent_data
        }
        
        # Get human-readable recommendation
        recommendation = advisor.get_human_recommendation(sample_inputs)
        print(recommendation)
        
        print("\n" + "="*60)
        print("SIMPLE SUMMARY:")
        print("-" * 20)
        
        # Get simple summary
        simple = advisor.get_simple_summary(sample_inputs)
        print(simple)
        
        print("\n" + "="*80)


if __name__ == "__main__":
    main()
