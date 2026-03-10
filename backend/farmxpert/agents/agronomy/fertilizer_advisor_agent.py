from __future__ import annotations
from typing import Dict, Any, List, Optional
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import FertilizerDatabaseTool, WeatherForecastTool, PlantGrowthSimulationTool, FertilizerTool
from farmxpert.services.gemini_service import gemini_service


class FertilizerAdvisorAgent(EnhancedBaseAgent):
    name = "fertilizer_advisor"
    description = "Provides comprehensive fertilizer recommendations based on crop stage, weather, and soil conditions"

    def _get_system_prompt(self) -> str:
        return """You are a Fertilizer Advisor Agent specializing in comprehensive fertilizer planning and recommendations.

Your expertise includes:
- Fertilizer database queries and recommendations
- Weather-based application scheduling
- Plant growth simulation and optimization
- Cost analysis and budget planning
- Organic and conventional fertilizer options
- Growth stage-specific applications

Always provide practical, cost-effective recommendations with clear implementation steps."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "What fertilizer should I use for wheat during vegetative stage?",
                "output": "For wheat in vegetative stage, I recommend urea (46-0-0) at 100 kg per acre applied as side dressing. Also consider DAP (18-46-0) for phosphorus needs. Apply when soil moisture is adequate and avoid application before heavy rainfall."
            },
            {
                "input": "How do I adjust my fertilizer schedule for upcoming rain?",
                "output": "If rain is expected within 24-48 hours, delay fertilizer application to prevent nutrient leaching. For urea, apply 2-3 days before rain for better absorption. Consider split applications during wet periods to minimize losses."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fertilizer recommendations using dynamic tools and comprehensive analysis"""
        try:
            # Get tools from inputs
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")
            
            # Extract parameters
            crop = self._extract_crop_from_query(query) or context.get("crop", "wheat")
            growth_stage = context.get("growth_stage", "vegetative")
            location = context.get("farm_location", inputs.get("location", "unknown"))
            soil_data = context.get("soil_data", {})
            area_acres = context.get("area_acres", 1.0)
            
            # Initialize data containers
            fertilizer_data = {}
            weather_data = {}
            growth_simulation_data = {}
            cost_analysis_data = {}
            
            # Get fertilizer database information
            if "fertilizer_database" in tools:
                try:
                    fertilizer_data = await tools["fertilizer_database"].query_fertilizer_database(
                        crop, growth_stage, soil_data, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get fertilizer database: {e}")
            
            # Get weather forecast for fertilizer planning
            if "weather_forecast" in tools:
                try:
                    weather_data = await tools["weather_forecast"].get_fertilizer_weather_forecast(location, days=14)
                except Exception as e:
                    self.logger.warning(f"Failed to get weather forecast: {e}")
            
            # Get plant growth simulation
            if "plant_growth_simulation" in tools and fertilizer_data:
                try:
                    growth_simulation_data = await tools["plant_growth_simulation"].simulate_plant_growth(
                        crop, fertilizer_data, soil_data, weather_data, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get growth simulation: {e}")
            
            # Get cost analysis
            if "fertilizer_database" in tools:
                try:
                    cost_analysis_data = await tools["fertilizer_database"].get_fertilizer_cost_analysis(
                        crop, area_acres, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to get cost analysis: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert fertilizer advisor. Based on the following comprehensive analysis, provide detailed fertilizer recommendations for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Crop: {crop}
- Growth Stage: {growth_stage}
- Location: {location}
- Area: {area_acres} acres
- Soil Data: {json.dumps(soil_data, indent=2)}
- Fertilizer Data: {fertilizer_data.get('fertilizer_types', [])}
- Weather Forecast: {weather_data.get('application_windows', {})}
- Growth Simulation: {growth_simulation_data.get('yield_estimates', {})}
- Cost Analysis: {cost_analysis_data.get('total_cost_breakdown', {})}

Provide comprehensive fertilizer recommendations including:
1. Specific fertilizer types and formulations
2. Application rates and timing
3. Application methods and equipment
4. Weather-based scheduling adjustments
5. Cost analysis and budget planning
6. Growth stage-specific applications
7. Risk management and monitoring
8. Expected outcomes and yield improvements

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "fertilizer_recommendations"})
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "crop": crop,
                    "growth_stage": growth_stage,
                    "location": location,
                    "area_acres": area_acres,
                    "fertilizer_data": fertilizer_data,
                    "weather_data": weather_data,
                    "growth_simulation_data": growth_simulation_data,
                    "cost_analysis_data": cost_analysis_data
                },
                "recommendations": self._extract_recommendations_from_data(fertilizer_data, cost_analysis_data),
                "warnings": self._extract_warnings_from_data(weather_data, growth_simulation_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in fertilizer advisor agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional fertilizer recommendation method"""
        crop = inputs.get("crop", "wheat")
        growth_stage = inputs.get("growth_stage", "vegetative")
        soil_npk = inputs.get("soil_npk", {"n": 50, "p": 30, "k": 40})
        weather_forecast = inputs.get("weather_forecast", {})
        
        schedule: List[Dict[str, Any]] = []
        
        if growth_stage == "seedling":
            schedule.append({
                "week": 1,
                "fertilizer": "Starter fertilizer (10-52-10)",
                "rate_per_acre": "50 kg",
                "method": "Broadcasting"
            })
        elif growth_stage == "vegetative":
            schedule.append({
                "week": 4,
                "fertilizer": "Urea (46-0-0)",
                "rate_per_acre": "100 kg",
                "method": "Side dressing"
            })
        elif growth_stage == "flowering":
            schedule.append({
                "week": 8,
                "fertilizer": "NPK (20-20-20)",
                "rate_per_acre": "75 kg",
                "method": "Foliar spray"
            })
            
        return {
            "agent": self.name,
            "success": True,
            "crop": crop,
            "current_stage": growth_stage,
            "fertilizer_schedule": schedule,
            "estimated_cost": 3500,
            "next_application_date": "2024-02-15",
            "metadata": {"source": "traditional"}
        }
    
    def _extract_crop_from_query(self, query: str) -> Optional[str]:
        """Extract mentioned crop from user query"""
        query_lower = query.lower()
        crops = ["wheat", "rice", "maize", "cotton", "sugarcane", "groundnut", "soybean", 
                "barley", "mustard", "chickpea", "lentil", "potato", "onion", "tomato"]
        
        for crop in crops:
            if crop in query_lower:
                return crop
        return None
    
    def _extract_recommendations_from_data(self, fertilizer_data: Dict[str, Any], cost_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(fertilizer_data, dict):
            if "fertilizer_types" in fertilizer_data:
                fertilizers = fertilizer_data["fertilizer_types"]
                if isinstance(fertilizers, list) and fertilizers:
                    recommendations.append(f"Recommended fertilizers: {', '.join(fertilizers[:3])}")
            
            if "application_rates" in fertilizer_data:
                recommendations.append("Application rates and timing provided")
        
        if isinstance(cost_analysis_data, dict):
            if "total_cost_breakdown" in cost_analysis_data:
                recommendations.append("Cost analysis and budget planning available")
        
        return recommendations
    
    def _extract_warnings_from_data(self, weather_data: Dict[str, Any], growth_simulation_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(weather_data, dict):
            if "weather_risks" in weather_data:
                risks = weather_data["weather_risks"]
                if isinstance(risks, list) and risks:
                    warnings.append(f"Weather risks: {', '.join(risks[:2])}")
        
        if isinstance(growth_simulation_data, dict):
            if "stress_indicators" in growth_simulation_data:
                stress = growth_simulation_data["stress_indicators"]
                if isinstance(stress, list) and stress:
                    warnings.append(f"Growth stress indicators: {', '.join(stress[:2])}")
        
        return warnings
