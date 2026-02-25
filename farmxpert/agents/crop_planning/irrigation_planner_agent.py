from __future__ import annotations
from typing import Dict, Any, List, Optional
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import EvapotranspirationModelTool, IoTSoilMoistureTool, WeatherAPITool, IrrigationTool
from farmxpert.services.gemini_service import gemini_service


class IrrigationPlannerAgent(EnhancedBaseAgent):
    name = "irrigation_planner"
    description = "Provides smart irrigation advice based on evapotranspiration, soil moisture sensors, and weather data"

    def _get_system_prompt(self) -> str:
        return """You are an Irrigation Planner Agent specializing in smart irrigation management and water optimization.

Your expertise includes:
- Evapotranspiration calculations and water requirement analysis
- IoT soil moisture sensor integration and real-time monitoring
- Weather-based irrigation scheduling and adjustments
- Water conservation and efficiency optimization
- Irrigation system recommendations and maintenance
- Cost-effective irrigation planning

Always provide practical, water-efficient irrigation recommendations with clear implementation steps."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "When should I irrigate my wheat field?",
                "output": "Based on your soil moisture levels and weather forecast, I recommend irrigating your wheat field in the early morning hours (5-7 AM) when evapotranspiration is low. Apply 15-20mm of water using drip irrigation for maximum efficiency."
            },
            {
                "input": "How much water does my rice field need?",
                "output": "For rice in the vegetative stage, you need approximately 25-30mm of water per week. With current soil moisture at 45%, I recommend applying 20mm of water over 3-4 hours using flood irrigation, preferably in the evening to minimize evaporation losses."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle irrigation planning using dynamic tools and comprehensive analysis"""
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
            field_size_acres = context.get("field_size_acres", inputs.get("field_size_acres", 1.0))
            sensor_data = context.get("sensor_data", {})
            
            # Initialize data containers
            et_data = {}
            sensor_analysis_data = {}
            weather_data = {}
            irrigation_optimization_data = {}
            
            # Get evapotranspiration calculations
            if "evapotranspiration_model" in tools:
                try:
                    weather_for_et = context.get("weather_data", {})
                    et_data = await tools["evapotranspiration_model"].calculate_evapotranspiration(
                        crop, growth_stage, weather_for_et, soil_data, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to calculate evapotranspiration: {e}")
            
            # Get IoT sensor data analysis
            if "iot_soil_moisture" in tools and sensor_data:
                try:
                    sensor_analysis_data = await tools["iot_soil_moisture"].integrate_sensor_data(
                        sensor_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to analyze sensor data: {e}")
            
            # Get weather forecast for irrigation
            if "weather_api" in tools:
                try:
                    weather_data = await tools["weather_api"].get_irrigation_weather_forecast(location, days=7)
                except Exception as e:
                    self.logger.warning(f"Failed to get weather forecast: {e}")
            
            # Get irrigation optimization
            if "evapotranspiration_model" in tools and et_data and sensor_analysis_data:
                try:
                    irrigation_optimization_data = await tools["evapotranspiration_model"].optimize_irrigation_schedule(
                        et_data, sensor_analysis_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to optimize irrigation schedule: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert irrigation planner. Based on the following comprehensive analysis, provide detailed irrigation recommendations for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Crop: {crop}
- Growth Stage: {growth_stage}
- Location: {location}
- Field Size: {field_size_acres} acres
- Soil Data: {json.dumps(soil_data, indent=2)}
- ET Data: {et_data.get('crop_et', {})}
- Sensor Data: {sensor_analysis_data.get('current_moisture', {})}
- Weather Forecast: {weather_data.get('irrigation_windows', {})}
- Optimization Data: {irrigation_optimization_data.get('irrigation_frequency', {})}

Provide comprehensive irrigation recommendations including:
1. Optimal irrigation timing and frequency
2. Water application rates and amounts
3. Irrigation method recommendations
4. Weather-based scheduling adjustments
5. Water conservation strategies
6. Cost optimization for irrigation
7. Monitoring and control recommendations
8. Expected water savings and efficiency gains

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "irrigation_planning"})
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "crop": crop,
                    "growth_stage": growth_stage,
                    "location": location,
                    "field_size_acres": field_size_acres,
                    "et_data": et_data,
                    "sensor_analysis_data": sensor_analysis_data,
                    "weather_data": weather_data,
                    "irrigation_optimization_data": irrigation_optimization_data
                },
                "recommendations": self._extract_recommendations_from_data(et_data, irrigation_optimization_data),
                "warnings": self._extract_warnings_from_data(weather_data, sensor_analysis_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in irrigation planner agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional irrigation planning method"""
        crop = inputs.get("crop", "wheat")
        season = inputs.get("season", "kharif")
        soil_moisture = inputs.get("soil_moisture", 60)
        weather = inputs.get("weather", {})
        field_size_acres = inputs.get("field_size_acres", 5)
        
        irrigation_schedule: List[Dict[str, Any]] = []
        
        if soil_moisture < 40:
            irrigation_schedule.append({
                "date": "2024-02-10",
                "duration_hours": 4,
                "water_amount_liters": 15000,
                "method": "drip irrigation"
            })
            
        irrigation_schedule.append({
            "date": "2024-02-17",
            "duration_hours": 3,
            "water_amount_liters": 12000,
            "method": "sprinkler"
        })
        
        return {
            "agent": self.name,
            "success": True,
            "crop": crop,
            "current_soil_moisture": soil_moisture,
            "irrigation_schedule": irrigation_schedule,
            "water_efficiency_score": 8.5,
            "estimated_weekly_cost": 1200,
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
    
    def _extract_recommendations_from_data(self, et_data: Dict[str, Any], irrigation_optimization_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(et_data, dict):
            if "daily_water_requirement" in et_data:
                recommendations.append("Daily water requirement calculated based on evapotranspiration")
            
            if "irrigation_scheduling" in et_data:
                recommendations.append("Optimal irrigation scheduling provided")
        
        if isinstance(irrigation_optimization_data, dict):
            if "irrigation_frequency" in irrigation_optimization_data:
                recommendations.append("Irrigation frequency optimized")
            
            if "water_savings" in irrigation_optimization_data:
                recommendations.append("Water conservation strategies available")
        
        return recommendations
    
    def _extract_warnings_from_data(self, weather_data: Dict[str, Any], sensor_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(weather_data, dict):
            if "weather_risks" in weather_data:
                risks = weather_data["weather_risks"]
                if isinstance(risks, list) and risks:
                    warnings.append(f"Weather risks: {', '.join(risks[:2])}")
        
        if isinstance(sensor_analysis_data, dict):
            if "anomaly_detection" in sensor_analysis_data:
                anomalies = sensor_analysis_data["anomaly_detection"]
                if isinstance(anomalies, list) and anomalies:
                    warnings.append(f"Sensor anomalies detected: {', '.join(anomalies[:2])}")
        
        return warnings
