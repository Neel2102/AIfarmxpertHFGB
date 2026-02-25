"""
Task Scheduler Agent Service for FarmXpert Main Project
Integrates task scheduling capabilities with orchestrator to access other agents
"""

import asyncio
import warnings
import os
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

# Suppress all warnings for this module
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

logger = logging.getLogger(__name__)

from .simple_service import simple_task_scheduler_service

TASK_SCHEDULER_AVAILABLE = False

# Import orchestrator client
from .orchestrator_client import task_scheduler_orchestrator_client


class TaskSchedulerService:
    """Service class for Task Scheduler Agent integration with orchestrator"""
    
    def __init__(self):
        """Initialize the Task Scheduler Service"""
        self.agent = simple_task_scheduler_service
        self.use_real_agent = False
    
    async def generate_daily_plan(self, 
                                 location: Dict[str, Any],
                                 crop_info: Dict[str, Any],
                                 resources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive daily farm task plan using data from all agents
        
        Args:
            location: Location data with city, state, coordinates
            crop_info: Crop information (name, growth_stage, area)
            resources: Resource constraints (labor, tractor_hours, pump_hours)
        """
        try:
            if not self.use_real_agent:
                return await self.agent.generate_daily_plan(location, crop_info, resources)
            
            # Step 1: Gather data from all agents via orchestrator
            print("Gathering data from all agents...")
            agent_data = await self.orchestrator_client.gather_agent_data(location, crop_info)
            
            # Step 2: Prepare context for task scheduler
            context = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "location": location,
                "crop_info": crop_info,
                "weather": agent_data.get("weather", {}).get("data", {}),
                "resources": resources or {
                    "labor": 2,
                    "tractor_hours": 4,
                    "pump_hours": 3
                }
            }
            
            # Step 3: Convert agent data to task scheduler format
            task_scheduler_data = self._convert_agent_data_to_tasks(agent_data)
            context.update(task_scheduler_data)
            
            # Step 4: Generate task plan
            print("📋 Generating task schedule...")
            result = await self.agent.handle(context, {})
            
            # Step 5: Enhance with agent-specific insights
            result = self._enhance_with_agent_insights(result, agent_data)
            
            # Step 6: Add LLM explanation if not present
            if not result.get("llm_explanation"):
                result["llm_explanation"] = await self._generate_comprehensive_explanation(result, agent_data)
            
            return {
                "success": True,
                "data": result,
                "agent_data_summary": self._summarize_agent_data(agent_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Task scheduling failed: {str(e)}",
                "error_type": "ProcessingError"
            }
    
    def _convert_agent_data_to_tasks(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert agent data to task scheduler format"""
        tasks = {}
        
        # Convert irrigation data
        irrigation_data = agent_data.get("irrigation", {})
        if irrigation_data.get("success") and irrigation_data.get("data"):
            irrigation = irrigation_data["data"]
            tasks["irrigation"] = {
                "action": irrigation.get("action", "INFO"),
                "details": irrigation.get("details", "Check irrigation needs"),
                "reason": "Based on current soil and weather conditions",
                "priority": irrigation.get("priority", "Medium")
            }
        
        # Convert fertilizer data
        fertilizer_data = agent_data.get("fertilizer", {})
        if fertilizer_data.get("success") and fertilizer_data.get("data"):
            fertilizer = fertilizer_data["data"]
            tasks["fertilizer"] = {
                "action": fertilizer.get("action", "INFO"),
                "details": " | ".join(fertilizer.get("details", [])) if isinstance(fertilizer.get("details"), list) else fertilizer.get("details", "Check fertilizer needs"),
                "reason": "Based on crop nutrient requirements",
                "priority": fertilizer.get("priority", "Medium")
            }
        
        # Convert soil health data
        soil_data = agent_data.get("soil_health", {})
        if soil_data.get("success") and soil_data.get("data"):
            soil = soil_data["data"]
            tasks["soil_health"] = {
                "action": soil.get("action", "INFO"),
                "details": " | ".join(soil.get("details", [])) if isinstance(soil.get("details"), list) else soil.get("details", "Monitor soil health"),
                "reason": "Based on current soil conditions",
                "priority": soil.get("priority", "Low")
            }
        
        # Convert growth data
        growth_data = agent_data.get("growth", {})
        if growth_data.get("success") and growth_data.get("data"):
            growth = growth_data["data"]
            tasks["growth_monitoring"] = {
                "action": growth.get("action", "MONITOR"),
                "details": " | ".join(growth.get("details", [])) if isinstance(growth.get("details"), list) else growth.get("details", "Monitor crop growth"),
                "reason": "Regular growth monitoring required",
                "priority": growth.get("priority", "Medium")
            }
        
        # Add weather-based tasks
        weather_data = agent_data.get("weather", {})
        if weather_data.get("success") and weather_data.get("data"):
            weather = weather_data["data"]
            if weather.get("rain_mm", 0) > 10:
                tasks["weather_protection"] = {
                    "action": "PROTECT",
                    "details": "Protect crops from heavy rain",
                    "reason": f"Heavy rain expected ({weather.get('rain_mm')}mm)",
                    "priority": "High"
                }
            elif weather.get("rain_mm", 0) == 0 and weather.get("current_temp", 25) > 35:
                tasks["heat_protection"] = {
                    "action": "PROTECT",
                    "details": "Provide shade and additional irrigation for heat protection",
                    "reason": f"High temperature expected ({weather.get('current_temp')}°C)",
                    "priority": "High"
                }
        
        return tasks
    
    def _enhance_with_agent_insights(self, result: Dict[str, Any], agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance task plan with insights from agents"""
        # Add weather-based warnings
        weather_data = agent_data.get("weather", {})
        if weather_data.get("success") and weather_data.get("data"):
            weather = weather_data["data"]
            warnings = result.get("warnings", [])
            
            if weather.get("rain_mm", 0) > 10:
                warnings.append("Heavy rain expected - avoid field operations")
            elif weather.get("current_temp", 25) > 35:
                warnings.append("High temperature - schedule tasks for early morning")
            
            result["warnings"] = warnings
        
        # Add agent-specific recommendations
        recommendations = result.get("recommendations", [])
        
        # Irrigation recommendations
        irrigation_data = agent_data.get("irrigation", {})
        if irrigation_data.get("success") and irrigation_data.get("data"):
            irrigation = irrigation_data["data"]
            if irrigation.get("water_requirement") == "high":
                recommendations.append("Increase irrigation frequency due to high water requirement")
        
        # Soil health recommendations
        soil_data = agent_data.get("soil_health", {})
        if soil_data.get("success") and soil_data.get("data"):
            soil = soil_data["data"]
            if soil.get("health_score", 70) < 60:
                recommendations.append("Consider soil amendment to improve health score")
        
        result["recommendations"] = recommendations
        
        return result
    
    def _summarize_agent_data(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of agent data for transparency"""
        summary = {}
        
        for agent_name, data in agent_data.items():
            if data.get("success"):
                summary[agent_name] = {
                    "status": "available",
                    "data_points": len(data.get("data", {})) if isinstance(data.get("data"), dict) else 1
                }
            else:
                summary[agent_name] = {
                    "status": "unavailable",
                    "error": data.get("error", "Unknown error")
                }
        
        return summary
    
    async def _generate_comprehensive_explanation(self, result: Dict[str, Any], agent_data: Dict[str, Any]) -> str:
        """Generate comprehensive explanation using all agent data"""
        try:
            # Import LLM service
            from farmxpert.app.orchestrator.services.llm_service import OrchestratorLLMService
            
            tasks = result.get("tasks_for_today", [])
            date = result.get("date", datetime.now().strftime("%Y-%m-%d"))
            crop = result.get("crop", "Unknown crop")
            growth_stage = result.get("growth_stage", "Unknown stage")
            
            # Build comprehensive prompt
            weather_info = agent_data.get("weather", {}).get("data", {})
            irrigation_info = agent_data.get("irrigation", {}).get("data", {})
            fertilizer_info = agent_data.get("fertilizer", {}).get("data", {})
            
            prompt = f"""
            Generate a comprehensive daily farm task plan summary for:
            Date: {date}
            Crop: {crop}
            Growth Stage: {growth_stage}
            
            Weather Conditions: {weather_info.get('conditions', 'Not available')} (Temp: {weather_info.get('current_temp', 'N/A')}°C, Rain: {weather_info.get('rain_mm', 'N/A')}mm)
            Irrigation Status: {irrigation_info.get('details', 'Not available')}
            Fertilizer Needs: {fertilizer_info.get('details', 'Not available')}
            
            Tasks for today:
            {chr(10).join([f"- {task.get('task', 'Unknown')}: {task.get('details', 'No details')} (Priority: {task.get('priority', 'Low')})" for task in tasks])}
            
            Provide a comprehensive, actionable summary in 4-5 sentences that incorporates weather conditions, agent recommendations, and practical farming guidance.
            """
            
            # Generate explanation
            explanation = await OrchestratorLLMService.generate_summary(
                query=f"Comprehensive daily farm plan for {crop}",
                weather_analysis=weather_info,
                growth_analysis=agent_data.get("growth", {}).get("data"),
                irrigation_analysis=irrigation_info,
                fertilizer_analysis=fertilizer_info,
                soil_health_analysis=agent_data.get("soil_health", {}).get("data"),
                market_intelligence_analysis=None,
                recommendations=[task.get('task', '') for task in tasks]
            )
            
            return explanation or f"Today's farm plan for {crop} includes {len(tasks)} tasks based on current conditions and agent recommendations."
            
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"Today's farm plan includes {len(tasks.get('tasks_for_today', []))} tasks based on current conditions and agent recommendations."
    
    async def update_task_status(self, 
                                task_name: str, 
                                task_date: str, 
                                status: str) -> Dict[str, Any]:
        """Update the status of a specific task"""
        try:
            if not self.use_real_agent:
                return {"success": False, "error": "Task tracking not available"}
            
            self.tracking_store.set_status(task_name, task_date, status)
            
            return {
                "success": True,
                "message": f"Task '{task_name}' status updated to '{status}'",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Task status update failed: {str(e)}"
            }
    
    async def get_task_status(self, task_name: str, task_date: str) -> Dict[str, Any]:
        """Get the current status of a specific task"""
        try:
            if not self.use_real_agent:
                return {"success": False, "error": "Task tracking not available"}
            
            status = self.tracking_store.get_status(task_name, task_date)
            
            return {
                "success": True,
                "task_name": task_name,
                "date": task_date,
                "status": status or "pending",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Task status retrieval failed: {str(e)}"
            }
    
    def _fallback_daily_plan(self, location: Dict[str, Any], crop_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback daily plan when task scheduler is not available"""
        crop_name = crop_info.get("crop", "Unknown crop")
        growth_stage = crop_info.get("growth_stage", "Unknown stage")
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "crop": crop_name,
            "growth_stage": growth_stage,
            "tasks_for_today": [
                {
                    "task": "General Farm Management",
                    "action": "PLAN",
                    "details": "Review and plan daily farm operations",
                    "reason": "Routine farm management",
                    "priority": "Medium"
                }
            ],
            "warnings": ["Task scheduler agent not available - using fallback plan"],
            "summary": "Basic farm plan generated - full task scheduling features not available",
            "llm_explanation": f"Basic farm management plan for {crop_name} in {growth_stage} stage. Consider implementing the full task scheduler for detailed planning with agent integration.",
            "agent_data_summary": {"status": "fallback_mode"}
        }


# Create singleton instance
task_scheduler_service = TaskSchedulerService()
