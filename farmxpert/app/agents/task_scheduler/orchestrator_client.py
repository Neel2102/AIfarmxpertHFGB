"""
Task Scheduler Orchestrator Client
Allows Task Scheduler to request data from other agents via orchestrator
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class TaskSchedulerOrchestratorClient:
    """Client for Task Scheduler to interact with other agents via orchestrator"""
    
    def __init__(self):
        # We'll import OrchestratorAgent only when needed to avoid conflicts
        self.orchestrator = None
    
    def _get_orchestrator(self):
        """Lazy import of OrchestratorAgent to avoid import conflicts"""
        if self.orchestrator is None:
            try:
                from farmxpert.app.orchestrator.agent import OrchestratorAgent
                self.orchestrator = OrchestratorAgent()
            except ImportError as e:
                print(f"⚠️ Could not import OrchestratorAgent: {e}")
                self.orchestrator = None
        return self.orchestrator
    
    async def gather_agent_data(self, location: Dict[str, Any], crop_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather data from all relevant agents for task scheduling
        
        Args:
            location: Location data (city, state, coordinates)
            crop_info: Crop information (name, growth_stage, area)
        
        Returns:
            Dictionary with data from weather, irrigation, fertilizer, soil, growth agents
        """
        try:
            orchestrator = self._get_orchestrator()
            if not orchestrator:
                return self._get_fallback_agent_data(crop_info)
            
            # Create requests for each agent
            agent_requests = {
                "weather": {
                    "query": f"weather forecast for {crop_info.get('crop', 'crops')} in {location.get('city', 'the farm')}",
                    "strategy": "auto",
                    "location": location,
                    "crop_data": crop_info
                },
                "irrigation": {
                    "query": f"irrigation needs for {crop_info.get('crop', 'crops')} in {crop_info.get('growth_stage', 'current stage')}",
                    "strategy": "auto",
                    "location": location,
                    "crop_data": crop_info
                },
                "fertilizer": {
                    "query": f"fertilizer recommendations for {crop_info.get('crop', 'crops')} in {crop_info.get('growth_stage', 'current stage')}",
                    "strategy": "auto",
                    "location": location,
                    "crop_data": crop_info
                },
                "soil_health": {
                    "query": f"soil health analysis for {crop_info.get('crop', 'crops')} farming",
                    "strategy": "auto",
                    "location": location,
                    "crop_data": crop_info
                },
                "growth": {
                    "query": f"growth stage monitoring for {crop_info.get('crop', 'crops')}",
                    "strategy": "auto",
                    "location": location,
                    "crop_data": crop_info
                }
            }
            
            # Execute all requests in parallel
            tasks = []
            for agent_name, request in agent_requests.items():
                task = self._call_agent(agent_name, request)
                tasks.append(task)
            
            # Wait for all agent responses
            agent_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process responses
            agent_data = {}
            agent_names = list(agent_requests.keys())
            
            for i, response in enumerate(agent_responses):
                agent_name = agent_names[i]
                
                if isinstance(response, Exception):
                    agent_data[agent_name] = {
                        "error": str(response),
                        "data": None
                    }
                else:
                    agent_data[agent_name] = self._extract_agent_data(response, agent_name)
            
            return agent_data
            
        except Exception as e:
            print(f"Error gathering agent data: {e}")
            return self._get_fallback_agent_data(crop_info)
    
    async def _call_agent(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific agent via orchestrator"""
        try:
            orchestrator = self._get_orchestrator()
            if not orchestrator:
                return {"error": "Orchestrator not available", "data": None}
            
            result = await orchestrator.handle_request(request)
            
            if result.get("error"):
                return {"error": result.get("error"), "data": None}
            
            data = result.get("data", {})
            results = data.get("results", {})
            
            # Extract specific agent data
            agent_mapping = {
                "weather": "weather",
                "irrigation": "irrigation", 
                "fertilizer": "fertilizer",
                "soil_health": "soil_health",
                "growth": "growth"
            }
            
            agent_key = agent_mapping.get(agent_name)
            if agent_key and agent_key in results:
                return {"data": results[agent_key], "success": True}
            else:
                return {"data": None, "success": False, "error": f"No data for {agent_name}"}
                
        except Exception as e:
            return {"error": str(e), "data": None}
    
    def _extract_agent_data(self, response: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Extract relevant data from agent response"""
        try:
            if response.get("error"):
                return {"error": response.get("error"), "data": None}
            
            data = response.get("data")
            if not data:
                return {"data": None, "success": False}
            
            # Extract based on agent type
            if agent_type == "weather":
                return self._extract_weather_data(data)
            elif agent_type == "irrigation":
                return self._extract_irrigation_data(data)
            elif agent_type == "fertilizer":
                return self._extract_fertilizer_data(data)
            elif agent_type == "soil_health":
                return self._extract_soil_data(data)
            elif agent_type == "growth":
                return self._extract_growth_data(data)
            else:
                return {"data": data, "success": True}
                
        except Exception as e:
            return {"error": str(e), "data": None}
    
    def _extract_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather data for task scheduling"""
        weather_data = data.get("data", {})
        
        return {
            "success": True,
            "data": {
                "current_temp": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "rain_mm": weather_data.get("rain_mm", 0),
                "wind_speed": weather_data.get("wind_speed"),
                "conditions": weather_data.get("conditions"),
                "forecast": weather_data.get("forecast", [])
            }
        }
    
    def _extract_irrigation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract irrigation data for task scheduling"""
        irrigation_data = data.get("data", {})
        
        return {
            "success": True,
            "data": {
                "action": irrigation_data.get("status", "INFO"),
                "details": irrigation_data.get("recommendation", "Check soil moisture"),
                "priority": irrigation_data.get("priority", "Medium"),
                "water_requirement": irrigation_data.get("water_requirement", "moderate")
            }
        }
    
    def _extract_fertilizer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fertilizer data for task scheduling"""
        fertilizer_data = data.get("data", {})
        
        return {
            "success": True,
            "data": {
                "action": "APPLY" if fertilizer_data.get("recommendations") else "INFO",
                "details": fertilizer_data.get("recommendations", ["No specific fertilizer needs"]),
                "priority": fertilizer_data.get("priority", "Low"),
                "nutrients": fertilizer_data.get("nutrients_required", [])
            }
        }
    
    def _extract_soil_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract soil health data for task scheduling"""
        soil_data = data.get("data", {})
        
        return {
            "success": True,
            "data": {
                "action": "TEST" if soil_data.get("health_score", 70) < 60 else "INFO",
                "details": soil_data.get("recommendations", ["Soil health is good"]),
                "priority": "High" if soil_data.get("health_score", 70) < 60 else "Low",
                "health_score": soil_data.get("health_score", 70)
            }
        }
    
    def _extract_growth_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract growth stage data for task scheduling"""
        growth_data = data.get("data", {})
        
        return {
            "success": True,
            "data": {
                "action": "MONITOR",
                "details": growth_data.get("recommendations", ["Continue monitoring crop growth"]),
                "priority": "Medium",
                "growth_stage": growth_data.get("growth_stage", "Unknown"),
                "health_status": growth_data.get("health_status", "Good")
            }
        }
    
    def _get_fallback_agent_data(self, crop_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback data when agents are not available"""
        crop_name = crop_info.get("crop", "crops")
        growth_stage = crop_info.get("growth_stage", "current stage")
        
        return {
            "weather": {
                "success": False,
                "data": None,
                "error": "Weather agent not available"
            },
            "irrigation": {
                "success": True,
                "data": {
                    "action": "IRRIGATE",
                    "details": f"Regular irrigation for {crop_name} in {growth_stage}",
                    "priority": "Medium"
                }
            },
            "fertilizer": {
                "success": True,
                "data": {
                    "action": "APPLY",
                    "details": f"Balanced fertilizer for {crop_name} in {growth_stage}",
                    "priority": "Medium"
                }
            },
            "soil_health": {
                "success": True,
                "data": {
                    "action": "INFO",
                    "details": "Soil health monitoring recommended",
                    "priority": "Low"
                }
            },
            "growth": {
                "success": True,
                "data": {
                    "action": "MONITOR",
                    "details": f"Monitor {crop_name} growth in {growth_stage}",
                    "priority": "Medium"
                }
            }
        }


# Create singleton instance
task_scheduler_orchestrator_client = TaskSchedulerOrchestratorClient()
