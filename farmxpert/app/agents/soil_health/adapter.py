"""
Soil Health Agent Adapter for FarmXpert Orchestrator
Optimized adapter that integrates with the new soil health architecture
"""

from typing import Dict, Any, Optional
from datetime import datetime
from farmxpert.app.agents.soil_health.services.soil_health_service import SoilHealthAnalysisService
from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput, QuickSoilCheckInput
from farmxpert.app.agents.soil_health.models.input_models import LocationInput, SoilSensorData
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response


class SoilHealthAgentAdapter:
    """Adapter for the optimized Soil Health Agent"""
    
    @staticmethod
    def analyze_soil_health(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze soil health using the optimized soil health agent
        
        Expected input format:
        {
            "location": {
                "latitude": float,
                "longitude": float,
                "district": str,
                "state": str
            },
            "soil_data": {
                "pH": float,
                "nitrogen": float,  # ppm
                "phosphorus": float,  # ppm  
                "potassium": float,  # ppm
                "electrical_conductivity": float,  # dS/m
                "moisture": float,  # optional
                "temperature": float  # optional
            },
            "crop_type": str,  # optional
            "growth_stage": str,  # optional
            "dynamic_soil_data": {}  # optional, from dynamic data service
        }
        """
        try:
            logger.info("🌱 Analyzing soil health with optimized agent")
            
            # Extract location
            location_data = request_data.get("location", {})
            if not location_data:
                return create_error_response(
                    "MISSING_LOCATION",
                    "Location data is required for soil health analysis",
                    {"request_data": request_data}
                )
            
            # Extract and enhance soil data
            soil_data = request_data.get("soil_data", {})
            dynamic_soil = request_data.get("dynamic_soil_data", {})
            
            # Create enhanced soil sensor data
            enhanced_soil_data = SoilHealthAgentAdapter._prepare_soil_data(
                soil_data, dynamic_soil
            )
            
            # Create location input
            location_input = LocationInput(
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                district=location_data.get("district", "Unknown"),
                state=location_data.get("state", "Unknown"),
                field_id=request_data.get("field_id")
            )
            
            # Create soil health input
            soil_health_input = SoilHealthInput(
                location=location_input,
                soil_data=enhanced_soil_data,
                crop_type=request_data.get("crop_type"),
                growth_stage=request_data.get("growth_stage"),
                triggered_at=request_data.get("timestamp", datetime.now()),
                request_source=request_data.get("request_source", "orchestrator"),
                field_id=request_data.get("field_id")
            )
            
            # Perform analysis
            analysis = SoilHealthAnalysisService.analyze_soil_health(soil_health_input)
            
            # Convert to orchestrator-friendly format
            result = {
                "agent": "soil_health_agent",
                "analysis_id": analysis.analysis_id,
                "health_score": analysis.health_score.overall_score,
                "health_breakdown": {
                    "pH_score": analysis.health_score.pH_score,
                    "nutrient_score": analysis.health_score.nutrient_score,
                    "salinity_score": analysis.health_score.salinity_score
                },
                "issues_detected": [
                    {
                        "problem": issue.problem.value,
                        "cause": issue.cause,
                        "effect": issue.effect,
                        "severity": issue.severity,
                        "urgency": issue.urgency.value
                    }
                    for issue in analysis.issues_detected
                ],
                "red_alert": analysis.red_alert,
                "recommendations": {
                    "chemical": [
                        {
                            "name": rec.name,
                            "description": rec.description,
                            "application_rate": rec.application_rate,
                            "timing": rec.timing
                        }
                        for rec in analysis.recommendations.chemical
                    ],
                    "organic": [
                        {
                            "name": rec.name,
                            "description": rec.description,
                            "application_rate": rec.application_rate,
                            "timing": rec.timing
                        }
                        for rec in analysis.recommendations.organic
                    ],
                    "cultural": [
                        {
                            "name": rec.name,
                            "description": rec.description,
                            "application_rate": rec.application_rate,
                            "timing": rec.timing
                        }
                        for rec in analysis.recommendations.cultural
                    ]
                },
                "soil_data_used": analysis.soil_data_analyzed.dict(),
                "location": analysis.location,
                "analyzed_at": analysis.analyzed_at.isoformat(),
                "crop_specific": bool(request_data.get("crop_type")),
                "data_sources": ["user_input", "dynamic_enrichment"] if dynamic_soil else ["user_input"]
            }
            
            return create_success_response(
                result,
                message="Soil health analysis completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Soil health adapter error: {e}")
            return create_error_response(
                "SOIL_HEALTH_ADAPTER_ERROR",
                f"Soil health analysis failed: {str(e)}",
                {"request_data": request_data}
            )
    
    @staticmethod
    def quick_soil_check(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick soil health check for orchestrator
        
        Expected input format:
        {
            "pH": float,
            "nitrogen": float,
            "phosphorus": float,
            "potassium": float,
            "electrical_conductivity": float,
            "moisture": float,  # optional
            "temperature": float  # optional
        }
        """
        try:
            logger.info("🌱 Performing quick soil health check")
            
            # Create quick check input
            quick_input = QuickSoilCheckInput(
                pH=request_data.get("pH", 7.0),
                nitrogen=request_data.get("nitrogen", 50),
                phosphorus=request_data.get("phosphorus", 20),
                potassium=request_data.get("potassium", 100),
                electrical_conductivity=request_data.get("electrical_conductivity", 1.5),
                moisture=request_data.get("moisture"),
                temperature=request_data.get("temperature")
            )
            
            # Perform quick check
            result = SoilHealthAnalysisService.quick_soil_check(quick_input)
            
            # Convert to orchestrator-friendly format
            return create_success_response(
                {
                    "agent": "soil_health_agent",
                    "health_score": result.health_score,
                    "red_alert": result.red_alert,
                    "issues_count": result.issues_count,
                    "overall_status": result.overall_status,
                    "urgency": result.urgency.value,
                    "top_recommendations": result.top_recommendations,
                    "checked_at": result.checked_at.isoformat()
                },
                message="Quick soil health check completed"
            )
            
        except Exception as e:
            logger.error(f"Quick soil check adapter error: {e}")
            return create_error_response(
                "QUICK_SOIL_CHECK_ADAPTER_ERROR",
                f"Quick soil health check failed: {str(e)}",
                {"request_data": request_data}
            )
    
    @staticmethod
    def _prepare_soil_data(user_soil_data: Dict[str, Any], dynamic_soil: Dict[str, Any]) -> SoilSensorData:
        """Prepare and enhance soil data with dynamic data"""
        
        # Start with user-provided data
        soil_data = {
            "pH": user_soil_data.get("pH"),
            "nitrogen": user_soil_data.get("nitrogen"),
            "phosphorus": user_soil_data.get("phosphorus"),
            "potassium": user_soil_data.get("potassium"),
            "electrical_conductivity": user_soil_data.get("electrical_conductivity"),
            "moisture": user_soil_data.get("moisture"),
            "temperature": user_soil_data.get("temperature"),
            "organic_matter": user_soil_data.get("organic_matter")
        }
        
        # Enhance with dynamic data if user data is missing
        if dynamic_soil:
            # Map dynamic data to expected fields
            dynamic_mapping = {
                "pH": dynamic_soil.get("ph_level"),
                "nitrogen": dynamic_soil.get("nitrogen_ppm"),
                "phosphorus": dynamic_soil.get("phosphorus_ppm"),
                "potassium": dynamic_soil.get("potassium_ppm"),
                "electrical_conductivity": dynamic_soil.get("electrical_conductivity"),
                "moisture": dynamic_soil.get("moisture_percent"),
                "temperature": dynamic_soil.get("temperature_celsius"),
                "organic_matter": dynamic_soil.get("organic_matter_percent")
            }
            
            # Fill missing values with dynamic data
            for key, dynamic_value in dynamic_mapping.items():
                if soil_data.get(key) is None and dynamic_value is not None:
                    soil_data[key] = dynamic_value
                    logger.info(f"Enhanced {key} with dynamic data: {dynamic_value}")
        
        # Set defaults for any remaining missing values
        defaults = {
            "pH": 6.5,
            "nitrogen": 50,
            "phosphorus": 20,
            "potassium": 100,
            "electrical_conductivity": 1.5,
            "moisture": 50.0,
            "temperature": 25.0,
            "organic_matter": 2.5
        }
        
        for key, default_value in defaults.items():
            if soil_data.get(key) is None:
                soil_data[key] = default_value
                logger.warning(f"Using default value for {key}: {default_value}")
        
        return SoilSensorData(**soil_data)


# Create simple interface functions for the orchestrator
def analyze_soil_health(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple interface function for comprehensive soil health analysis"""
    return SoilHealthAgentAdapter.analyze_soil_health(request_data)


def quick_soil_check(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple interface function for quick soil health check"""
    return SoilHealthAgentAdapter.quick_soil_check(request_data)
