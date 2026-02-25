"""
Weather Watcher Router
API endpoints for weather monitoring agent
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .agent import WeatherWatcherAgent
from farmxpert.app.shared.utils import logger
from farmxpert.app.shared.exceptions import FarmXpertException

router = APIRouter()

@router.get("/")
async def weather_info():
    """Get weather watcher information"""
    return {
        "name": "Weather Watcher Agent",
        "description": "Provides localized weather intelligence and actionable farming advice for Indian farmers",
        "version": "2.0.0",
        "capabilities": [
            "Current weather analysis",
            "7-day weather forecasting",
            "Rainfall probability analysis",
            "Dry spell detection",
            "Heat stress warnings",
            "Actionable farming advice",
            "Village-level localization",
            "Farmer-friendly recommendations"
        ],
        "supported_features": {
            "weather_data": ["temperature", "rainfall", "humidity", "wind_speed", "rainfall_probability"],
            "risk_alerts": ["HEAT_STRESS", "HEAVY_RAIN", "DRY_SPELL", "HIGH_RAIN_PROBABILITY", "HIGH_WIND"],
            "farming_actions": ["irrigation", "sowing", "pesticide_application", "harvest_protection"],
            "forecast_range": "7 days",
            "localization": ["village", "district", "state"]
        }
    }

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_weather(request: Dict[str, Any]):
    """
    Analyze weather conditions and generate comprehensive farming intelligence
    
    Args:
        request: Dictionary containing location and analysis options
        Example: {
            "location": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "village": "Sample Village",
                "district": "Sample District",
                "state": "Sample State"
            }
        }
        
    Returns:
        Weather intelligence with summary, risk alerts, and actionable farming advice
    """
    try:
        logger.info(f"🌦️ Received weather analysis request")
        
        # Extract location from request
        location = request.get("location", {})
        
        if not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail={
                "error": True,
                "error_code": "INVALID_LOCATION",
                "message": "Latitude and longitude are required"
            })
        
        # Call agent for analysis
        result = WeatherWatcherAgent.analyze_weather(location)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Weather analysis failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in weather analysis: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during weather analysis"
        })

@router.post("/alerts", response_model=Dict[str, Any])
async def get_weather_alerts(location: Dict[str, Any]):
    """
    Get weather alerts and farming advice for a location
    
    Args:
        location: Dictionary containing latitude and longitude
        Example: {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "village": "Sample Village",
            "district": "Sample District",
            "state": "Sample State"
        }
        
    Returns:
        Weather risk alerts and actionable farming advice
    """
    try:
        logger.info(f"🚨 Received weather alerts request")
        
        if not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail={
                "error": True,
                "error_code": "INVALID_LOCATION",
                "message": "Latitude and longitude are required"
            })
        
        # Call agent for alerts
        result = WeatherWatcherAgent.get_weather_alerts(location)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Weather alerts failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in weather alerts: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during weather alerts generation"
        })

@router.post("/farmer-message", response_model=Dict[str, Any])
async def get_farmer_message(request: Dict[str, Any]):
    """
    Get farmer-friendly weather message for a location
    
    Args:
        request: Dictionary containing location
        Example: {
            "location": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "village": "Sample Village",
                "district": "Sample District",
                "state": "Sample State"
            }
        }
        
    Returns:
        Farmer-friendly weather message with actionable advice
    """
    try:
        logger.info(f"🌾 Received farmer message request")
        
        # Extract location from request
        location = request.get("location", {})
        
        if not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail={
                "error": True,
                "error_code": "INVALID_LOCATION",
                "message": "Latitude and longitude are required"
            })
        
        # Call agent for farmer message
        result = WeatherWatcherAgent.get_farmer_message(location)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Farmer message generation failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in farmer message generation: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during farmer message generation"
        })

@router.get("/health")
async def weather_health():
    """Health check for weather watcher agent"""
    return {
        "status": "healthy",
        "agent": "weather_watcher",
        "timestamp": "2026-01-30T11:39:00Z",
        "services": {
            "weather_service": "active",
            "rule_engine": "active",
            "llm_service": "active"
        }
    }
