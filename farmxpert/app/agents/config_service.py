"""
Unified Agent Configuration Service
Central configuration management for all FarmXpert agents
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AgentConfigService:
    """Central service for managing unified agent configurations"""
    
    def __init__(self):
        self.config_file = Path(__file__).parent / "unified_config.json"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Configuration file not found: {self.config_file}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file doesn't exist"""
        return {
            "weather_watcher": {
                "name": "Weather Watcher Agent",
                "description": "Monitors weather conditions and provides agricultural insights",
                "capabilities": ["weather_forecasting", "temperature_monitoring", "humidity_tracking", "rainfall_analysis", "weather_alerts"],
                "endpoints": ["/weather", "/weather/analyze"],
                "data_sources": ["OpenWeatherMap", "WeatherAPI"],
                "status": "active"
            },
            "growth_stage_monitor": {
                "name": "Growth Stage Monitor",
                "description": "Analyzes crop growth stages and health status",
                "capabilities": ["stage_estimation", "health_assessment", "disease_detection", "growth_prediction"],
                "endpoints": ["/growth/analyze", "/growth/stage"],
                "data_sources": ["crop_database", "image_analysis"],
                "status": "active"
            },
            "irrigation_agent": {
                "name": "Irrigation Agent",
                "description": "Provides irrigation recommendations and scheduling",
                "capabilities": ["irrigation_planning", "moisture_analysis", "water_usage_optimization", "irrigation_scheduling"],
                "endpoints": ["/irrigation/analyze", "/irrigation/schedule"],
                "data_sources": ["soil_moisture_sensors", "weather_data", "crop_database"],
                "status": "active"
            },
            "fertilizer_agent": {
                "name": "Fertilizer Agent",
                "description": "Analyzes soil conditions and provides fertilizer recommendations",
                "capabilities": ["soil_analysis", "nutrient_recommendations", "fertilizer_planning"],
                "endpoints": ["/fertilizer/analyze", "/fertilizer/recommend"],
                "data_sources": ["soil_database", "nutrient_database"],
                "status": "active"
            },
            "soil_health_agent": {
                "name": "Soil Health Agent",
                "description": "Analyzes soil health and provides management recommendations",
                "capabilities": ["soil_testing", "health_assessment", "nutrient_analysis", "soil_recommendations"],
                "endpoints": ["/soil/analyze", "/soil/health"],
                "data_sources": ["soil_sensors", "soil_database"],
                "status": "active"
            },
            "market_intelligence_agent": {
                "name": "Market Intelligence Agent",
                "description": "Provides market price analysis and selling recommendations",
                "capabilities": ["price_tracking", "market_trends", "revenue_projection", "selling_optimization", "market_intelligence"],
                "endpoints": ["/market/analyze", "/market/prices"],
                "data_sources": ["market_data_apis", "historical_prices"],
                "status": "active"
            },
            "task_scheduler_agent": {
                "name": "Task Scheduler Agent",
                "description": "Manages farming tasks and schedules",
                "capabilities": ["task_creation", "task_scheduling", "task_prioritization", "deadline_tracking"],
                "endpoints": ["/tasks/create", "/tasks/list", "/tasks/update"],
                "data_sources": ["task_database", "crop_database"],
                "status": "active"
            }
        }
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent"""
        return self._config.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """Get all agent configurations"""
        return self._config
    
    def get_active_agents(self) -> Dict[str, Any]:
        """Get only active agents"""
        return {k: v for k, v in self._config.items() if v.get("status") == "active"}
    
    def get_agent_endpoints(self, agent_name: str) -> list:
        """Get endpoints for a specific agent"""
        config = self.get_agent_config(agent_name)
        return config.get("endpoints", []) if config else []
    
    def get_agent_capabilities(self, agent_name: str) -> list:
        """Get capabilities for a specific agent"""
        config = self.get_agent_config(agent_name)
        return config.get("capabilities", []) if config else []
    
    def get_agent_data_sources(self, agent_name: str) -> list:
        """Get data sources for a specific agent"""
        config = self.get_agent_config(agent_name)
        return config.get("data_sources", []) if config else []
    
    def update_agent_status(self, agent_name: str, status: str) -> bool:
        """Update agent status in configuration"""
        try:
            if agent_name in self._config:
                self._config[agent_name]["status"] = status
                self._save_config()
                logger.info(f"Updated {agent_name} status to: {status}")
                return True
            else:
                logger.warning(f"Agent {agent_name} not found in configuration")
                return False
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def validate_agent_input(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize input data for any agent"""
        config = self.get_agent_config(agent_name)
        if not config:
            logger.warning(f"No configuration found for agent: {agent_name}")
            return input_data
        
        # Standardize input based on agent requirements
        standardized_input = {}
        
        # Common fields for all agents
        common_fields = {
            "farmer_id": input_data.get("farmer_id", "farmer_001"),
            "field_id": input_data.get("field_id", "field_001"),
            "location": input_data.get("location", {}),
            "timestamp": input_data.get("timestamp", ""),
            "request_source": input_data.get("request_source", "api"),
            "query": input_data.get("query", "")  # Preserve query for all agents
        }
        standardized_input.update(common_fields)
        
        # Agent-specific standardization
        if agent_name == "weather_watcher":
            standardized_input.update({
                "city": input_data.get("location", {}).get("city", ""),
                "coordinates": {
                    "latitude": input_data.get("location", {}).get("latitude"),
                    "longitude": input_data.get("location", {}).get("longitude")
                }
            })
        
        elif agent_name == "growth_stage_monitor":
            crop_data = input_data.get("crop", {})
            standardized_input.update({
                "crop": {
                    "crop_name": crop_data.get("crop_name", crop_data.get("name", "unknown")),
                    "variety": crop_data.get("variety"),
                    "sowing_date": crop_data.get("sowing_date"),
                    "area_hectares": crop_data.get("area_hectares", 1.0)
                }
            })
        
        elif agent_name == "irrigation_agent":
            crop_data = input_data.get("crop", {})
            standardized_input.update({
                "crop": crop_data.get("crop_name", crop_data.get("name", "unknown")),
                "area_acres": crop_data.get("area_hectares", 1.0) * 2.47,  # Convert to acres
                "growth_stage": input_data.get("growth_stage", "vegetative"),
                "soil_type": input_data.get("soil_type", "loamy"),
                "soil_moisture_percent": input_data.get("soil_moisture_percent", 50.0),
                "soil_moisture_measured_at": input_data.get("soil_moisture_measured_at"),
                "rain_last_3_days_mm": input_data.get("rain_last_3_days_mm", 0),
                "rain_forecast_next_5_days": input_data.get("rain_forecast_next_5_days", [])
            })
        
        elif agent_name == "fertilizer_agent":
            crop_data = input_data.get("crop", {})
            standardized_input.update({
                "crop": crop_data.get("crop_name", crop_data.get("name", "unknown")),
                "area_hectares": crop_data.get("area_hectares", 1.0),
                "soil_type": input_data.get("soil_type", "loamy"),
                "growth_stage": input_data.get("growth_stage", "vegetative")
            })
        
        elif agent_name == "soil_health_agent":
            standardized_input.update({
                "soil_type": input_data.get("soil_type", "loamy"),
                "depth_cm": input_data.get("depth_cm", [0, 10, 20]),
                "location": input_data.get("location", {})
            })
        
        elif agent_name == "market_intelligence_agent":
            crop_data = input_data.get("crop", {}) or input_data.get("crop_data", {})
            location_data = input_data.get("location", {})
            farm_data = input_data.get("farm", {})
            standardized_input.update({
                "crop_info": {
                    "name": crop_data.get("crop_name", crop_data.get("name", "unknown")),
                    "area_hectares": crop_data.get("area_hectares", 1.0),
                    "expected_yield_quintals_per_hectare": farm_data.get("expected_yield_quintals_per_hectare")
                },
                "location": {
                    "state": location_data.get("state", ""),
                    "district": location_data.get("district", ""),
                    "city": location_data.get("city", "")
                }
            })
        
        elif agent_name == "task_scheduler_agent":
            crop_data = input_data.get("crop", {})
            standardized_input.update({
                "crop_info": {
                    "name": crop_data.get("crop_name", crop_data.get("name", "unknown")),
                    "area_hectares": crop_data.get("area_hectares", 1.0)
                },
                "preferences": input_data.get("preferences", {})
            })
        
        return standardized_input


# Create singleton instance
agent_config_service = AgentConfigService()
