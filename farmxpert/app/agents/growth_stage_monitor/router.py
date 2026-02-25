"""
Growth Stage Monitor Router
API endpoints for crop growth monitoring agent
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .agent import GrowthStageMonitorAgent
from farmxpert.app.shared.utils import logger
from farmxpert.app.shared.exceptions import FarmXpertException

router = APIRouter()

@router.get("/")
async def growth_info():
    """Get growth stage monitor information"""
    return {
        "name": "Growth Stage Monitor Agent",
        "description": "Monitors crop growth stages and health",
        "version": "1.0.0",
        "capabilities": [
            "Growth stage identification",
            "Health status assessment",
            "Weather correlation analysis",
            "LLM-powered explanations",
            "Multi-crop support"
        ]
    }

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_growth(request: Dict[str, Any]):
    """
    Analyze crop growth stage and health
    
    Args:
        request: Dictionary containing crop data, location, and images
        
    Returns:
        Growth analysis results with stage assessment, health status, and recommendations
    """
    try:
        logger.info(f"🌱 Received growth analysis request for farmer: {request.get('farmer_id', 'unknown')}")
        
        # Call agent for analysis
        result = GrowthStageMonitorAgent.analyze_growth(request)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except FarmXpertException as e:
        logger.error(f"Growth analysis failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in growth analysis: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during growth analysis"
        })

@router.post("/stage")
async def get_growth_stage(crop_data: Dict[str, Any]):
    """
    Get growth stage for a crop
    
    Args:
        crop_data: Basic crop information for stage estimation
        
    Returns:
        Growth stage assessment
    """
    try:
        logger.info(f"🔍 Received growth stage request")
        
        # Call agent for stage analysis
        result = GrowthStageMonitorAgent.analyze_growth(crop_data)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result)
        
        # Return only stage assessment
        return {
            "success": True,
            "stage_assessment": result["data"]["stage_assessment"],
            "crop_info": result["data"]["crop_info"],
            "timestamp": result["timestamp"]
        }
        
    except FarmXpertException as e:
        logger.error(f"Growth stage estimation failed: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": True,
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in growth stage estimation: {e}")
        raise HTTPException(status_code=500, detail={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error during growth stage estimation"
        })

@router.get("/health")
async def growth_health():
    """Health check for growth stage monitor agent"""
    return {
        "status": "healthy",
        "agent": "growth_stage_monitor",
        "timestamp": "2026-01-30T11:39:00Z",
        "services": {
            "growth_stage_engine": "active",
            "growth_health_engine": "active",
            "weather_correlation": "active",
            "llm_service": "active"
        }
    }
