"""
Enhanced Crop Selector Agent for FarmXpert
Provides intelligent crop recommendations using LLM capabilities
"""

from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent


class EnhancedCropSelectorAgent(EnhancedBaseAgent):
    """
    Enhanced Crop Selector Agent
    Provides intelligent crop recommendations based on soil, weather, market, and farm conditions
    """
    
    def __init__(self):
        super().__init__(
            name="Enhanced Crop Selector Agent",
            description="AI-powered crop selection expert that analyzes multiple factors to recommend optimal crops",
            use_llm=True,
            max_retries=3,
            temperature=0.7
        )
    
    def _get_system_prompt(self) -> str:
        """Get the specialized system prompt for crop selection"""
        return """You are an expert agricultural crop selection specialist with deep knowledge of:

1. **Crop Requirements**: Soil pH, nutrient needs, climate preferences, water requirements
2. **Seasonal Planning**: Optimal planting times, crop rotation strategies, seasonal market demands
3. **Market Intelligence**: Current market prices, demand trends, export opportunities
4. **Risk Assessment**: Weather risks, pest susceptibility, market volatility
5. **Sustainability**: Environmental impact, soil health preservation, resource efficiency

Your role is to analyze farm conditions and provide:
- Top 3-5 crop recommendations with detailed reasoning
- Specific planting and management advice
- Market timing recommendations
- Risk mitigation strategies
- Expected yield and profitability estimates

Always consider the farmer's location, soil conditions, available resources, and market conditions."""
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example conversations for crop selection"""
        return [
            {
                "input": "I have 5 hectares in ahmedabad, soil pH 7.2, planning for Rabi season. What should I plant?",
                "output": "Based on your conditions, I recommend: 1) Wheat (optimal for Rabi, good market demand), 2) Mustard (oilseed, good rotation crop), 3) Chickpea (pulse, soil improvement). Consider soil testing for NPK levels."
            },
            {
                "input": "My farm is in Karnataka, red soil, monsoon season. Looking for high-value crops.",
                "output": "For your red soil and monsoon conditions: 1) Turmeric (high value, good export demand), 2) Ginger (medicinal value, good market), 3) Black pepper (climber, high returns). Ensure proper drainage for these crops."
            }
        ]
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools available for crop selection"""
        return [
            {
                "name": "Soil Analysis",
                "description": "Analyze soil test results for crop suitability"
            },
            {
                "name": "Weather Assessment",
                "description": "Evaluate weather patterns and seasonal conditions"
            },
            {
                "name": "Market Analysis",
                "description": "Assess current market prices and demand trends"
            },
            {
                "name": "Risk Evaluation",
                "description": "Identify and mitigate farming risks"
            }
        ]
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using traditional logic (fallback)"""
        soil = inputs.get("soil", {})
        season = inputs.get("season", "unknown")
        location = inputs.get("location", "unknown")
        
        # Basic crop recommendations based on season and location
        if season.lower() in ["rabi", "winter"]:
            suggested = ["wheat", "mustard", "chickpea", "barley"]
        elif season.lower() in ["kharif", "monsoon"]:
            suggested = ["rice", "maize", "cotton", "sugarcane"]
        else:
            suggested = ["pulses", "vegetables", "fruits"]
        
        return {
            "agent": self.name,
            "success": True,
            "response": f"Based on {season} season in {location}, I recommend: {', '.join(suggested)}",
            "recommendations": suggested,
            "data": {
                "location": location,
                "season": season,
                "soil_summary": {k: soil.get(k) for k in ("ph", "npk", "organic") if k in soil},
                "suggested_crops": suggested,
                "method": "traditional"
            },
            "metadata": {
                "method": "traditional",
                "confidence": 0.6
            }
        }
    
    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced handle method for crop selection
        """
        # Add query if not present
        if "query" not in inputs:
            inputs["query"] = self._generate_query_from_inputs(inputs)
        
        return await super().handle(inputs)
    
    def _generate_query_from_inputs(self, inputs: Dict[str, Any]) -> str:
        """Generate a natural language query from structured inputs"""
        parts = []
        
        if inputs.get("location"):
            parts.append(f"farm in {inputs['location']}")
        
        if inputs.get("season"):
            parts.append(f"planning for {inputs['season']} season")
        
        if inputs.get("soil"):
            soil = inputs["soil"]
            if isinstance(soil, dict) and soil:
                soil_parts = []
                if "ph" in soil:
                    soil_parts.append(f"soil pH {soil['ph']}")
                if "npk" in soil:
                    soil_parts.append(f"NPK levels available")
                if "organic" in soil:
                    soil_parts.append(f"organic matter {soil['organic']}%")
                
                if soil_parts:
                    parts.append(f"with {', '.join(soil_parts)}")
        
        if inputs.get("farm_size"):
            parts.append(f"farm size {inputs['farm_size']} hectares")
        
        if not parts:
            parts.append("planning crop selection")
        
        query = f"What crops should I plant for {' '.join(parts)}?"
        return query
    
    async def get_crop_recommendations(
        self,
        location: str,
        season: str,
        soil_data: Dict[str, Any],
        farm_size: float = None,
        market_preference: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Get specialized crop recommendations
        """
        inputs = {
            "query": f"Recommend crops for {location} in {season} season with soil data: {soil_data}",
            "location": location,
            "season": season,
            "soil": soil_data,
            "farm_size": farm_size,
            "market_preference": market_preference,
            "use_llm": True
        }
        
        return await self.handle(inputs)
    
    async def analyze_crop_suitability(
        self,
        crop_name: str,
        location: str,
        soil_data: Dict[str, Any],
        season: str
    ) -> Dict[str, Any]:
        """
        Analyze suitability of a specific crop
        """
        inputs = {
            "query": f"Is {crop_name} suitable for {location} in {season} season? Analyze soil requirements and provide detailed assessment.",
            "crop_name": crop_name,
            "location": location,
            "season": season,
            "soil": soil_data,
            "use_llm": True
        }
        
        return await self.handle(inputs)
    
    async def get_crop_rotation_plan(
        self,
        location: str,
        current_crops: List[str],
        soil_health: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get crop rotation recommendations
        """
        inputs = {
            "query": f"Create a crop rotation plan for {location} considering current crops: {current_crops} and soil health: {soil_health}",
            "location": location,
            "current_crops": current_crops,
            "soil_health": soil_health,
            "use_llm": True
        }
        
        return await self.handle(inputs)
    
    async def get_market_timing_advice(
        self,
        crop_name: str,
        location: str,
        season: str
    ) -> Dict[str, Any]:
        """
        Get market timing advice for crop planning
        """
        inputs = {
            "query": f"What is the optimal planting and harvesting timing for {crop_name} in {location} during {season} season? Consider market demand and prices.",
            "crop_name": crop_name,
            "location": location,
            "season": season,
            "use_llm": True
        }
        
        return await self.handle(inputs)
