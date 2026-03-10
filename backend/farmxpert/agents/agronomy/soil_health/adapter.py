"""
Soil Health Agent Adapter for FarmXpert Orchestrator
Optimized adapter that integrates with the new soil health architecture
"""

from typing import Dict, Any, Optional
from datetime import datetime
from farmxpert.agents.agronomy.soil_health_agent import SoilHealthAgent
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response


class SoilHealthAgentAdapter:
    """Adapter for the optimized Soil Health Agent"""
    
    @staticmethod
    async def analyze_soil_health(request_data: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.info("Analyzing soil health with optimized agent")

            # Delegate to the canonical SoilHealthAgent implementation.
            # Note: this keeps the adapter stable while avoiding dependency on moved service/model modules.
            agent = SoilHealthAgent()
            agent_input: Dict[str, Any] = {
                "query": request_data.get("query") or "soil_health",
                "context": request_data,
            }

            result = await agent.handle(agent_input)
            return create_success_response(result, message="Soil health analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Soil health adapter error: {e}")
            return create_error_response(
                "SOIL_HEALTH_ADAPTER_ERROR",
                f"Soil health analysis failed: {str(e)}",
                {"request_data": request_data}
            )
    
    @staticmethod
    async def quick_soil_check(request_data: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.info("Performing quick soil health check")

            agent = SoilHealthAgent()
            agent_input: Dict[str, Any] = {
                "query": request_data.get("query") or "soil_health",
                "context": request_data,
            }

            result = await agent.handle(agent_input)
            return create_success_response(result, message="Quick soil health check completed")
            
        except Exception as e:
            logger.error(f"Quick soil check adapter error: {e}")
            return create_error_response(
                "QUICK_SOIL_CHECK_ADAPTER_ERROR",
                f"Quick soil health check failed: {str(e)}",
                {"request_data": request_data}
            )
    
    @staticmethod
    def _prepare_soil_data(user_soil_data: Dict[str, Any], dynamic_soil: Dict[str, Any]) -> Dict[str, Any]:
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
        
        return soil_data


# Create simple interface functions for the orchestrator
async def analyze_soil_health(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple interface function for comprehensive soil health analysis"""
    return await SoilHealthAgentAdapter.analyze_soil_health(request_data)


async def quick_soil_check(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple interface function for quick soil health check"""
    return await SoilHealthAgentAdapter.quick_soil_check(request_data)


def analyze_soil_health_sync(_request_data: Dict[str, Any]) -> Dict[str, Any]:
    raise RuntimeError("analyze_soil_health is async; call await analyze_soil_health(...) from an async context")


def quick_soil_check_sync(_request_data: Dict[str, Any]) -> Dict[str, Any]:
    raise RuntimeError("quick_soil_check is async; call await quick_soil_check(...) from an async context")
