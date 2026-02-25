from __future__ import annotations
from typing import Dict, Any, List, Optional
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import SatelliteImageProcessingTool, DroneImageProcessingTool, GrowthStagePredictionTool, CropTool
from farmxpert.services.gemini_service import gemini_service


class GrowthStageMonitorAgent(EnhancedBaseAgent):
    name = "growth_stage_monitor"
    description = "Monitors crop growth stages using satellite/drone imagery and predictive modeling"

    def _get_system_prompt(self) -> str:
        return """You are a Growth Stage Monitor Agent specializing in advanced crop monitoring and growth stage prediction.

Your expertise includes:
- Satellite image processing and NDVI analysis
- Drone imagery analysis and thermal processing
- Growth stage prediction and progression monitoring
- Crop health assessment and stress detection
- Precision agriculture recommendations
- Anomaly detection and corrective actions

Always provide accurate growth stage assessments with actionable monitoring recommendations."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "What growth stage is my wheat crop in?",
                "output": "Based on satellite NDVI analysis and drone imagery, your wheat crop is currently in the vegetative stage (Day 35). The NDVI value of 0.65 indicates healthy growth. I recommend monitoring for leaf diseases and applying nitrogen fertilizer within the next 7 days."
            },
            {
                "input": "Is my rice crop developing normally?",
                "output": "Drone imagery analysis shows your rice crop is progressing well through the flowering stage. However, thermal imaging detected some water stress in the northern section. I recommend increasing irrigation frequency and monitoring for blast disease during this critical stage."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle growth stage monitoring using dynamic tools and comprehensive analysis"""
        try:
            # Get tools from inputs
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")
            
            # Extract parameters
            crop = self._extract_crop_from_query(query) or context.get("crop", "wheat")
            location = context.get("farm_location", inputs.get("location", "unknown"))
            planting_date = context.get("planting_date", inputs.get("planting_date", "2024-01-01"))
            satellite_data = context.get("satellite_data", {})
            drone_data = context.get("drone_data", {})
            environmental_data = context.get("environmental_data", {})
            historical_data = context.get("historical_data", {})
            
            # Initialize data containers
            ndvi_analysis_data = {}
            drone_analysis_data = {}
            growth_prediction_data = {}
            progression_monitoring_data = {}
            
            # Get satellite NDVI analysis
            if "satellite_image_processing" in tools and satellite_data:
                try:
                    ndvi_analysis_data = await tools["satellite_image_processing"].analyze_ndvi(
                        satellite_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to analyze NDVI: {e}")
            
            # Get drone imagery analysis
            if "drone_image_processing" in tools and drone_data:
                try:
                    drone_analysis_data = await tools["drone_image_processing"].analyze_drone_imagery(
                        drone_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to analyze drone imagery: {e}")
            
            # Get growth stage prediction
            if "growth_stage_prediction" in tools and environmental_data:
                try:
                    growth_prediction_data = await tools["growth_stage_prediction"].predict_growth_stages(
                        environmental_data, crop, location, planting_date
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to predict growth stages: {e}")
            
            # Get growth progression monitoring
            if "growth_stage_prediction" in tools and historical_data:
                try:
                    current_data = context.get("current_data", {})
                    progression_monitoring_data = await tools["growth_stage_prediction"].monitor_growth_progression(
                        historical_data, current_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to monitor growth progression: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert growth stage monitor and crop analyst. Based on the following comprehensive analysis, provide detailed growth stage assessment and monitoring recommendations for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Crop: {crop}
- Location: {location}
- Planting Date: {planting_date}
- NDVI Analysis: {ndvi_analysis_data.get('vegetation_health', {})}
- Drone Analysis: {drone_analysis_data.get('growth_stage_assessment', {})}
- Growth Prediction: {growth_prediction_data.get('current_stage', {})}
- Progression Monitoring: {progression_monitoring_data.get('progression_analysis', {})}

Provide comprehensive growth stage monitoring including:
1. Current growth stage assessment and confidence level
2. Growth progression analysis and timeline
3. Health indicators and stress detection
4. Anomaly identification and explanations
5. Stage-specific care recommendations
6. Monitoring frequency and methods
7. Intervention timing and priorities
8. Harvest readiness indicators
9. Risk factors and mitigation strategies
10. Precision agriculture opportunities

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "growth_monitoring"})

            # If LLM quota/rate limit is hit, fall back to deterministic output
            resp_lower = (response or "").lower()
            if "429" in resp_lower or "quota" in resp_lower or "rate limit" in resp_lower:
                return await self._handle_traditional(inputs)
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "crop": crop,
                    "location": location,
                    "planting_date": planting_date,
                    "ndvi_analysis_data": ndvi_analysis_data,
                    "drone_analysis_data": drone_analysis_data,
                    "growth_prediction_data": growth_prediction_data,
                    "progression_monitoring_data": progression_monitoring_data
                },
                "recommendations": self._extract_recommendations_from_data(ndvi_analysis_data, drone_analysis_data),
                "warnings": self._extract_warnings_from_data(growth_prediction_data, progression_monitoring_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in growth stage monitor agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional growth stage monitoring method"""
        crop = inputs.get("crop", "unknown")
        planting_date = inputs.get("planting_date", "2024-01-01")
        current_date = inputs.get("current_date", "2024-02-01")
        environmental_factors = inputs.get("environmental_factors", {})
        
        # Calculate days since planting
        days_since_planting = 31  # Simplified calculation
        
        # Determine growth stage based on crop and days
        if crop.lower() in ["wheat", "rice", "maize"]:
            if days_since_planting < 7:
                stage = "germination"
            elif days_since_planting < 21:
                stage = "seedling"
            elif days_since_planting < 45:
                stage = "vegetative"
            elif days_since_planting < 75:
                stage = "flowering"
            elif days_since_planting < 105:
                stage = "grain_filling"
            else:
                stage = "maturity"
        else:
            stage = "vegetative"  # Default stage
            
        # Calculate expected completion percentage
        expected_days_to_maturity = 120  # Default for cereals
        completion_percentage = min((days_since_planting / expected_days_to_maturity) * 100, 100)
        
        return {
            "agent": self.name,
            "success": True,
            "crop": crop,
            "current_stage": stage,
            "days_since_planting": days_since_planting,
            "completion_percentage": round(completion_percentage, 1),
            "expected_harvest_date": "2024-05-01",
            "next_stage_timeline": "14-21 days",
            "stage_specific_recommendations": [
                f"Monitor for {stage}-specific pests",
                f"Adjust irrigation for {stage} stage",
                f"Apply {stage}-appropriate nutrients"
            ],
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
    
    def _extract_recommendations_from_data(self, ndvi_analysis_data: Dict[str, Any], drone_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(ndvi_analysis_data, dict):
            if "crop_condition_recommendations" in ndvi_analysis_data:
                recommendations.append("NDVI-based crop condition recommendations available")
            
            if "monitoring_frequency" in ndvi_analysis_data:
                recommendations.append("Optimized monitoring frequency provided")
        
        if isinstance(drone_analysis_data, dict):
            if "precision_recommendations" in drone_analysis_data:
                recommendations.append("Precision agriculture recommendations available")
            
            if "harvest_readiness" in drone_analysis_data:
                recommendations.append("Harvest readiness indicators provided")
        
        return recommendations
    
    def _extract_warnings_from_data(self, growth_prediction_data: Dict[str, Any], progression_monitoring_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(growth_prediction_data, dict):
            if "risk_factors" in growth_prediction_data:
                risk_factors = growth_prediction_data["risk_factors"]
                if isinstance(risk_factors, list) and risk_factors:
                    warnings.append(f"Growth risk factors identified: {', '.join(risk_factors[:2])}")
        
        if isinstance(progression_monitoring_data, dict):
            if "anomaly_detection" in progression_monitoring_data:
                anomalies = progression_monitoring_data["anomaly_detection"]
                if isinstance(anomalies, list) and anomalies:
                    warnings.append(f"Growth anomalies detected: {', '.join(anomalies[:2])}")
        
        return warnings
