"""
Soil Health Agent Router
API endpoints for soil health analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
from farmxpert.agents.agronomy.soil_health_agent import SoilHealthAgent
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.services.providers.blynk_iot_provider import blynk_iot_provider
from farmxpert.services.gemini_service import gemini_service

router = APIRouter()


@router.get("/iot/latest")
async def get_latest_iot_soil_data():
    """Fetch latest soil sensor readings from hardware IoT (Blynk)."""
    try:
        payload = await blynk_iot_provider.get_soil_sensor_payload()
        if not payload.get("success"):
            return create_error_response(
                "IOT_UNAVAILABLE",
                payload.get("error") or "IoT provider unavailable",
                {"provider": "Blynk"},
            )
        return create_success_response(payload)
    except Exception as e:
        return create_error_response(
            "IOT_FETCH_FAILED",
            str(e),
            {"provider": "Blynk"},
        )

@router.get("/")
async def soil_health_info():
    """Get soil health agent information"""
    return {
        "name": "Soil Health Agent",
        "description": "Analyzes soil health parameters and provides recommendations",
        "version": "2.0.0",
        "architecture": "Optimized for FarmXpert modular monolith",
        "capabilities": [
            "Soil pH analysis",
            "Nutrient level assessment (N, P, K)",
            "Salinity detection",
            "Chemical and organic recommendations",
            "Health scoring",
            "Crop-specific analysis",
            "Location-aware recommendations"
        ],
        "models": {
            "input": ["SoilHealthInput", "QuickSoilCheckInput"],
            "output": ["SoilHealthAnalysis", "QuickSoilCheckResult"]
        },
        "services": ["SoilHealthAnalysisService"],
        "constraints": ["soil_constraints.py with crop-specific thresholds"],
        "endpoints": [
            "/agents/soil_health/analyze",
            "/agents/soil_health/quick_check"
        ]
    }

@router.post("/analyze")
async def analyze_soil(request: Dict[str, Any]):
    """
    Comprehensive soil health analysis
    
    Request format:
    {
        "location": {
            "latitude": 21.7051,
            "longitude": 72.9959,
            "district": "Ankleshwar",
            "state": "Gujarat"
        },
        "soil_data": {
            "pH": 6.5,
            "nitrogen": 50,
            "phosphorus": 20,
            "potassium": 100,
            "electrical_conductivity": 1.5,
            "moisture": 35.0,
            "temperature": 18.0
        },
        "crop_type": "cotton",
        "growth_stage": "vegetative"
    }
    """
    try:
        logger.info("Received comprehensive soil health analysis request")
        agent = SoilHealthAgent()
        agent_input: Dict[str, Any] = {
            "query": request.get("query") or "soil_health",
            "context": request,
        }
        return await agent.handle(agent_input)

    except Exception as e:
        logger.error(f"Soil health analysis error: {e}")
        return create_error_response(
            "SOIL_HEALTH_ANALYSIS_ERROR",
            str(e),
            {"request": request},
        )

@router.post("/quick_check")
async def quick_soil_check(request: Dict[str, Any]):
    """
    Quick soil health check with minimal parameters
    
    Request format:
    {
        "pH": 6.5,
        "nitrogen": 50,
        "phosphorus": 20,
        "potassium": 100,
        "electrical_conductivity": 1.5,
        "moisture": 35.0,
        "temperature": 18.0
    }
    """
    try:
        logger.info("Received quick soil health check")

        agent = SoilHealthAgent()
        agent_input: Dict[str, Any] = {
            "query": request.get("query") or "soil_health",
            "context": request,
        }
        return await agent.handle(agent_input)
        
    except Exception as e:
        logger.error(f"Quick soil check error: {e}")
        return create_error_response(
            "QUICK_SOIL_CHECK_ERROR",
            str(e),
            {"request": request}
        )

@router.get("/health")
async def soil_health_agent_health():
    """Health check for soil health agent"""
    return {
        "status": "healthy",
        "agent": "soil_health_agent",
        "version": "2.0.0",
        "timestamp": "2026-02-03T22:15:00Z",
        "architecture": "FarmXpert modular monolith optimized",
        "capabilities": [
            "soil_ph_analysis",
            "nutrient_assessment", 
            "salinity_detection",
            "recommendation_generation",
            "health_scoring",
            "crop_specific_analysis",
            "location_aware_recommendations"
        ],
        "parameters_monitored": [
            "pH", "nitrogen", "phosphorus", "potassium", 
            "electrical_conductivity", "moisture", "temperature"
        ],
        "supported_crops": [
            "cotton", "wheat", "rice", "maize", "default"
        ],
        "models_loaded": True,
        "constraints_loaded": True,
        "services_active": 1
    }
