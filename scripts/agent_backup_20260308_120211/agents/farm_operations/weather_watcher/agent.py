"""
Weather Watcher Agent
Core logic for weather monitoring and alert generation
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .services.weather_service import WeatherService
from .services.rule_engine import RuleEngine
from .services.llm_service import LLMService
from .services.farmer_message_service import generate_farmer_message
from .models.weather_models import WeatherSnapshot, WeatherForecast
from .models.output_models import WeatherAlertOutput
from app.shared.utils import logger, create_success_response, create_error_response
from app.shared.exceptions import WeatherServiceException, LLMServiceException


class WeatherWatcherAgent:
    """Weather monitoring and alert generation agent"""
    
    @staticmethod
    def get_farmer_message(location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate farmer-friendly weather message for a location
        
        Args:
            location: Dictionary containing latitude and longitude
            
        Returns:
            Farmer-friendly weather message with actionable advice
        """
        try:
            logger.info(f"🌾 Generating farmer message for location: {location}")
            
            # Extract coordinates
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            if not latitude or not longitude:
                return create_error_response(
                    "INVALID_LOCATION",
                    "Latitude and longitude are required",
                    {"location": location}
                )
            
            # Get current weather
            current_weather = WeatherService.get_weather(latitude, longitude)
            
            if not current_weather:
                return create_error_response(
                    "WEATHER_FETCH_FAILED",
                    "Failed to fetch weather data",
                    {"coordinates": {"lat": latitude, "lon": longitude}}
                )
            
            # Get weather forecast for enhanced analysis
            forecasts = WeatherService.get_weather_forecast(latitude, longitude, days=7)
            
            # Generate comprehensive farming intelligence using rule engine
            rule_engine = RuleEngine(last_alerts={})
            weather_intelligence = rule_engine.evaluate(current_weather, forecasts)
            
            # Add location info
            location_info = {
                "latitude": latitude,
                "longitude": longitude,
                "village": location.get("village"),
                "district": location.get("district"),
                "state": location.get("state")
            }
            
            # Generate farmer-friendly message
            farmer_message = generate_farmer_message(weather_intelligence, location_info)
            
            return create_success_response(
                farmer_message,
                message=f"Farmer-friendly weather message generated for coordinates ({latitude}, {longitude})",
                metadata={
                    "temperature": current_weather.temperature,
                    "condition": current_weather.weather_condition,
                    "rainfall_probability": current_weather.rainfall_probability,
                    "alert_count": len(weather_intelligence.risk_alerts),
                    "action_count": len(weather_intelligence.farming_actions),
                    "forecast_available": len(forecasts) > 0,
                    "location": location_info
                }
            )
            
        except WeatherServiceException as e:
            logger.error(f"Weather service error: {e.message}")
            return create_error_response(
                e.error_code or "WEATHER_ERROR",
                e.message,
                e.details
            )
        except Exception as e:
            logger.error(f"Unexpected error in farmer message generation: {e}")
            return create_error_response(
                "UNEXPECTED_ERROR",
                f"Unexpected error: {str(e)}",
                {"location": location}
            )
    
    @staticmethod
    def analyze_weather(location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze weather conditions for a given location with farming intelligence
        
        Args:
            location: Dictionary containing latitude and longitude
            
        Returns:
            Dictionary with comprehensive weather analysis and farming advice
        """
        try:
            logger.info(f"🌦️ Analyzing weather for location: {location}")
            
            # Extract coordinates
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            if not latitude or not longitude:
                return create_error_response(
                    "INVALID_LOCATION",
                    "Latitude and longitude are required",
                    {"location": location}
                )
            
            # Get current weather
            current_weather = WeatherService.get_weather(latitude, longitude)
            
            if not current_weather:
                return create_error_response(
                    "WEATHER_FETCH_FAILED",
                    "Failed to fetch weather data",
                    {"coordinates": {"lat": latitude, "lon": longitude}}
                )
            
            # Get weather forecast for enhanced analysis
            forecasts = WeatherService.get_weather_forecast(latitude, longitude, days=7)
            
            # Generate comprehensive farming intelligence using rule engine
            rule_engine = RuleEngine(last_alerts={})
            weather_intelligence = rule_engine.evaluate(current_weather, forecasts)
            
            # Add location info
            weather_intelligence.location_info = {
                "latitude": latitude,
                "longitude": longitude,
                "village": location.get("village"),
                "district": location.get("district"),
                "state": location.get("state")
            }
            
            # Prepare response data in expected format
            response_data = {
                "location": location,
                "weather_summary": weather_intelligence.weather_summary.model_dump(),
                "risk_alerts": [alert.model_dump() for alert in weather_intelligence.risk_alerts],
                "farming_actions": [action.model_dump() for action in weather_intelligence.farming_actions],
                "current_weather": current_weather.model_dump(),
                "forecast_available": len(forecasts) > 0,
                "forecast_days": len(forecasts),
                "analysis_summary": f"Weather intelligence generated for coordinates ({latitude}, {longitude})",
                "generated_at": weather_intelligence.generated_at.isoformat()
            }
            
            # Add forecast summary if available
            if forecasts:
                response_data["forecast_summary"] = {
                    "next_3_days_rainfall": sum(f.rainfall_mm for f in forecasts[:3]),
                    "next_7_days_rainfall": sum(f.rainfall_mm for f in forecasts),
                    "avg_temperature_3_days": sum(f.temperature for f in forecasts[:3]) / min(3, len(forecasts))
                }
            
            # Add LLM explanation for complex scenarios if any alerts
            if weather_intelligence.risk_alerts:
                try:
                    # Create a simple summary for LLM explanation
                    alert_summary = {
                        "current_temp": current_weather.temperature,
                        "current_rain": current_weather.rainfall_mm,
                        "alerts": [{"type": a.alert_type, "severity": a.severity, "message": a.message} 
                                 for a in weather_intelligence.risk_alerts],
                        "actions": [{"action": a.action, "priority": a.priority} 
                                  for a in weather_intelligence.farming_actions[:3]]  # Top 3 actions
                    }
                    explanation = LLMService.explain_alert(alert_summary)
                    response_data["llm_explanation"] = explanation
                except Exception as e:
                    logger.warning(f"LLM explanation failed: {e}")
                    response_data["llm_explanation"] = "Unable to generate explanation"
            
            return create_success_response(
                response_data,
                message=f"Weather intelligence completed for coordinates ({latitude}, {longitude})",
                metadata={
                    "temperature": current_weather.temperature,
                    "condition": current_weather.weather_condition,
                    "rainfall_probability": current_weather.rainfall_probability,
                    "alert_count": len(weather_intelligence.risk_alerts),
                    "action_count": len(weather_intelligence.farming_actions),
                    "forecast_available": len(forecasts) > 0
                }
            )
            
        except WeatherServiceException as e:
            logger.error(f"Weather service error: {e.message}")
            return create_error_response(
                e.error_code or "WEATHER_ERROR",
                e.message,
                e.details
            )
        except Exception as e:
            logger.error(f"Unexpected error in weather analysis: {e}")
            return create_error_response(
                "UNEXPECTED_ERROR",
                f"Unexpected error: {str(e)}",
                {"location": location}
            )
    
    @staticmethod
    def get_weather_alerts(location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather alerts and farming advice for a location
        
        Args:
            location: Dictionary containing latitude and longitude
            
        Returns:
            Dictionary with weather alerts and actionable farming advice
        """
        try:
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            if not latitude or not longitude:
                return create_error_response(
                    "INVALID_LOCATION",
                    "Latitude and longitude are required"
                )
            
            # Get current weather data
            current_weather = WeatherService.get_weather(latitude, longitude)
            
            if not current_weather:
                return create_error_response(
                    "WEATHER_FETCH_FAILED",
                    "Failed to fetch weather data"
                )
            
            # Get weather forecast for enhanced analysis
            forecasts = WeatherService.get_weather_forecast(latitude, longitude, days=7)
            
            # Generate alerts and farming actions
            rule_engine = RuleEngine(last_alerts={})
            weather_intelligence = rule_engine.evaluate(current_weather, forecasts)
            
            # Add location info
            weather_intelligence.location_info = {
                "latitude": latitude,
                "longitude": longitude,
                "village": location.get("village"),
                "district": location.get("district"),
                "state": location.get("state")
            }
            
            return create_success_response(
                {
                    "location": location,
                    "weather_summary": weather_intelligence.weather_summary.model_dump(),
                    "risk_alerts": [alert.model_dump() for alert in weather_intelligence.risk_alerts],
                    "farming_actions": [action.model_dump() for action in weather_intelligence.farming_actions],
                    "alert_count": len(weather_intelligence.risk_alerts),
                    "action_count": len(weather_intelligence.farming_actions),
                    "forecast_available": len(forecasts) > 0,
                    "generated_at": weather_intelligence.generated_at.isoformat()
                },
                message=f"Generated {len(weather_intelligence.risk_alerts)} risk alerts and {len(weather_intelligence.farming_actions)} farming actions"
            )
            
        except Exception as e:
            logger.error(f"Error getting weather alerts: {e}")
            return create_error_response(
                "ALERT_GENERATION_FAILED",
                f"Failed to generate alerts: {str(e)}"
            )
