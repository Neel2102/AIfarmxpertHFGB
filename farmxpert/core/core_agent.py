"""
Core Agent Router - Single Agent to Rule Them All
Replaces 22+ individual agents with one intelligent router that changes personality based on role.
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from farmxpert.services.gemini_service import gemini_service
from farmxpert.services.tools import (
    SoilTool, WeatherTool, MarketTool, CropTool, FertilizerTool, 
    PestDiseaseTool, IrrigationTool, WebScrapingTool, ClimatePredictionTool, 
    MarketAnalysisTool, GeneticDatabaseTool, SoilSuitabilityTool, 
    YieldPredictionTool, SoilSensorTool, AmendmentRecommendationTool, 
    LabTestAnalyzerTool, FertilizerDatabaseTool, WeatherForecastTool, 
    PlantGrowthSimulationTool, EvapotranspirationModelTool, 
    IoTSoilMoistureTool, WeatherAPITool, ImageRecognitionTool, 
    VoiceToTextTool, DiseasePredictionTool, WeatherMonitoringTool, 
    AlertSystemTool, SatelliteImageProcessingTool, DroneImageProcessingTool, 
    GrowthStagePredictionTool, TaskPrioritizationTool, RealTimeTrackingTool, 
    MaintenanceTrackerTool, PredictiveMaintenanceTool, FieldMappingTool, 
    YieldModelTool, ProfitOptimizationTool, MarketIntelligenceTool, 
    LogisticsTool, ProcurementTool, InsuranceRiskTool, FarmerCoachTool, 
    ComplianceCertificationTool, CommunityEngagementTool, CarbonSustainabilityTool
)
from farmxpert.core.utils.logger import get_logger

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class CoreAgent:
    """
    Single intelligent agent that routes requests and adapts personality based on role.
    Replaces the complexity of 22+ individual agents with one robust, maintainable solution.
    """
    
    def __init__(self):
        self.logger = get_logger("core_agent")
        self.prompts = self._load_agent_prompts()
        self.tools = self._initialize_tools()
        
    def _load_agent_prompts(self) -> Dict[str, Any]:
        """Load agent prompts from JSON configuration file"""
        prompts_file = PROJECT_ROOT / "farmxpert" / "core" / "agent_prompts.json"
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
                return prompts_data.get("agents", {})
        except FileNotFoundError:
            self.logger.error(f"Agent prompts file not found: {prompts_file}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing agent prompts: {e}")
            return {}
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize all available tools for the agent"""
        return {
            "soil": SoilTool(),
            "weather": WeatherTool(),
            "market": MarketTool(),
            "crop": CropTool(),
            "fertilizer": FertilizerTool(),
            "pest_disease": PestDiseaseTool(),
            "irrigation": IrrigationTool(),
            "web_scraping": WebScrapingTool(),
            "climate_prediction": ClimatePredictionTool(),
            "market_analysis": MarketAnalysisTool(),
            "genetic_database": GeneticDatabaseTool(),
            "soil_suitability": SoilSuitabilityTool(),
            "yield_prediction": YieldPredictionTool(),
            "soil_sensor": SoilSensorTool(),
            "amendment_recommendation": AmendmentRecommendationTool(),
            "lab_test_analyzer": LabTestAnalyzerTool(),
            "fertilizer_database": FertilizerDatabaseTool(),
            "weather_forecast": WeatherForecastTool(),
            "plant_growth_simulation": PlantGrowthSimulationTool(),
            "evapotranspiration_model": EvapotranspirationModelTool(),
            "iot_soil_moisture": IoTSoilMoistureTool(),
            "weather_api": WeatherAPITool(),
            "image_recognition": ImageRecognitionTool(),
            "voice_to_text": VoiceToTextTool(),
            "disease_prediction": DiseasePredictionTool(),
            "weather_monitoring": WeatherMonitoringTool(),
            "alert_system": AlertSystemTool(),
            "satellite_image_processing": SatelliteImageProcessingTool(),
            "drone_image_processing": DroneImageProcessingTool(),
            "growth_stage_prediction": GrowthStagePredictionTool(),
            "task_prioritization": TaskPrioritizationTool(),
            "real_time_tracking": RealTimeTrackingTool(),
            "maintenance_tracker": MaintenanceTrackerTool(),
            "predictive_maintenance": PredictiveMaintenanceTool(),
            "field_mapping": FieldMappingTool(),
            "yield_model": YieldModelTool(),
            "profit_optimization": ProfitOptimizationTool(),
            "market_intelligence": MarketIntelligenceTool(),
            "logistics": LogisticsTool(),
            "procurement": ProcurementTool(),
            "insurance_risk": InsuranceRiskTool(),
            "farmer_coach": FarmerCoachTool(),
            "compliance_cert": ComplianceCertificationTool(),
            "community": CommunityEngagementTool(),
            "carbon_sustainability": CarbonSustainabilityTool()
        }
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent roles"""
        return list(self.prompts.keys())
    
    def get_agent_info(self, agent_role: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent role"""
        return self.prompts.get(agent_role)
    
    async def process_request(
        self, 
        user_input: str, 
        agent_role: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to process user requests with specified agent role
        
        Args:
            user_input: The user's query or request
            agent_role: The role/personality to adopt (e.g., "soil_health", "crop_selector")
            context: Additional context information
            session_id: Session identifier for tracking
            
        Returns:
            Agent response with recommendations, insights, and data
        """
        start_time = datetime.now()
        
        try:
            # Validate agent role
            if agent_role not in self.prompts:
                return self._create_error_response(
                    f"Unknown agent role: {agent_role}. Available roles: {', '.join(self.get_available_agents())}",
                    start_time
                )
            
            agent_config = self.prompts[agent_role]
            
            # Gather tool data based on agent's required tools
            tool_data = await self._gather_tool_data(
                agent_config.get("tools", []),
                user_input,
                context,
                session_id
            )
            
            # Construct the enhanced prompt
            enhanced_prompt = self._construct_prompt(
                agent_config,
                user_input,
                tool_data,
                context
            )
            
            # Call Gemini API
            self.logger.info(f"Processing request with agent role: {agent_role}")
            gemini_response = await gemini_service.generate_response(
                enhanced_prompt,
                {"task": agent_role, "session_id": session_id}
            )
            
            # Parse and structure the response
            structured_response = self._parse_gemini_response(
                gemini_response,
                agent_role,
                tool_data,
                start_time
            )
            
            self.logger.info(f"Successfully processed request with {agent_role} agent")
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Error processing request with {agent_role} agent: {e}", exc_info=True)
            return self._create_error_response(str(e), start_time)
    
    async def _gather_tool_data(
        self, 
        required_tools: List[str], 
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gather data from required tools for the agent"""
        tool_data = {}
        context = context or {}
        
        for tool_name in required_tools:
            if tool_name in self.tools:
                try:
                    tool = self.tools[tool_name]
                    
                    # Call tool with relevant context
                    tool_context = {
                        "query": user_input,
                        "session_id": session_id,
                        "user_id": context.get("user_id"),
                        **context
                    }
                    
                    # Different tools might have different methods
                    if hasattr(tool, 'load_static'):
                        data = tool.load_static(tool_context)
                    elif hasattr(tool, 'get_data'):
                        data = tool.get_data(tool_context)
                    elif hasattr(tool, 'fetch'):
                        data = tool.fetch(tool_context)
                    else:
                        data = {"status": "Tool available but no suitable method found"}
                    
                    tool_data[tool_name] = data
                    self.logger.debug(f"Gathered data from {tool_name} tool")
                    
                except Exception as e:
                    self.logger.warning(f"Error gathering data from {tool_name} tool: {e}")
                    tool_data[tool_name] = {"error": str(e)}
        
        return tool_data
    
    def _construct_prompt(
        self, 
        agent_config: Dict[str, Any], 
        user_input: str,
        tool_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct the enhanced prompt for Gemini"""
        
        # Base system prompt
        system_prompt = agent_config.get("system_prompt", "")
        
        # Add examples if available
        examples = agent_config.get("examples", [])
        examples_text = ""
        if examples:
            examples_text = "\n\nExamples of good responses:\n"
            for i, example in enumerate(examples, 1):
                examples_text += f"\nExample {i}:\nInput: {example.get('input', '')}\nOutput: {example.get('output', '')}\n"
        
        # Add tool data
        tool_data_text = ""
        if tool_data:
            tool_data_text = "\n\nAvailable Tool Data:\n"
            for tool_name, data in tool_data.items():
                if isinstance(data, dict) and not data.get("error"):
                    tool_data_text += f"- {tool_name}: {json.dumps(data, indent=2)}\n"
        
        # Add context
        context_text = ""
        if context:
            context_text = f"\n\nAdditional Context: {json.dumps(context, indent=2)}"
        
        # Construct final prompt
        final_prompt = f"""{system_prompt}{examples_text}

Current User Query: {user_input}{tool_data_text}{context_text}

Please provide a comprehensive response following these guidelines:
1. Be specific and actionable
2. Use the available tool data to inform your response
3. Provide clear recommendations
4. Include any relevant warnings or considerations
5. Suggest next steps when appropriate

Format your response as a helpful, expert advisor."""
        
        return final_prompt
    
    def _parse_gemini_response(
        self, 
        gemini_response: str, 
        agent_role: str,
        tool_data: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Parse and structure the Gemini response"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract recommendations, warnings, and next steps from response
        response_lines = gemini_response.split('\n')
        recommendations = []
        warnings = []
        next_steps = []
        
        current_section = None
        for line in response_lines:
            line = line.strip()
            if line.lower().startswith('recommendation'):
                current_section = 'recommendations'
            elif line.lower().startswith('warning'):
                current_section = 'warnings'
            elif line.lower().startswith('next step'):
                current_section = 'next_steps'
            elif line and current_section:
                if current_section == 'recommendations':
                    recommendations.append(line)
                elif current_section == 'warnings':
                    warnings.append(line)
                elif current_section == 'next_steps':
                    next_steps.append(line)
        
        # If no structured sections found, treat the whole response as the main response
        if not recommendations and not warnings and not next_steps:
            main_response = gemini_response
        else:
            main_response = gemini_response
        
        return {
            "agent": agent_role,
            "success": True,
            "response": main_response,
            "recommendations": recommendations[:5],  # Limit to 5 recommendations
            "warnings": warnings[:3],  # Limit to 3 warnings
            "next_steps": next_steps[:5],  # Limit to 5 next steps
            "data": {
                "tool_data": tool_data,
                "agent_config": {
                    "name": self.prompts[agent_role].get("name"),
                    "description": self.prompts[agent_role].get("description"),
                    "category": self.prompts[agent_role].get("category")
                }
            },
            "metadata": {
                "execution_time": execution_time,
                "tools_used": list(tool_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_error_response(self, error_message: str, start_time: datetime) -> Dict[str, Any]:
        """Create a standardized error response"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "agent": "core_agent",
            "success": False,
            "response": f"I apologize, but I encountered an error: {error_message}",
            "recommendations": ["Please try rephrasing your query", "Check if the agent role is correct"],
            "warnings": ["Service temporarily unavailable"],
            "next_steps": ["Try again in a few moments", "Contact support if issue persists"],
            "data": {},
            "metadata": {
                "execution_time": execution_time,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Global instance for easy access
core_agent = CoreAgent()

async def process_farm_request(
    user_input: str, 
    agent_role: str, 
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for processing farm requests
    
    Args:
        user_input: The user's query
        agent_role: The role to process the request
        context: Additional context
        session_id: Session identifier
        
    Returns:
        Structured response from the agent
    """
    return await core_agent.process_request(user_input, agent_role, context, session_id)

# Example usage and testing
if __name__ == "__main__":
    async def test_core_agent():
        """Test the core agent with different roles"""
        
        # Test soil health agent
        response = await process_farm_request(
            "My soil pH is 5.8, what should I do?",
            "soil_health",
            {"location": "Punjab", "crop": "wheat"}
        )
        print("Soil Health Response:", response["response"])
        
        # Test crop selector agent
        response = await process_farm_request(
            "What crops should I plant this season?",
            "crop_selector",
            {"season": "Kharif", "location": "Maharashtra"}
        )
        print("Crop Selector Response:", response["response"])
        
        # Test market intelligence agent
        response = await process_farm_request(
            "What are wheat prices now?",
            "market_intelligence",
            {"location": "Delhi"}
        )
        print("Market Intelligence Response:", response["response"])
    
    # Run test
    asyncio.run(test_core_agent())
