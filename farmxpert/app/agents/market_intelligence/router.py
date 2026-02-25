"""
FastAPI Router for Market Intelligence Agent
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio

from .models import (
    QuickAnalysisRequest, ComprehensiveAnalysisRequest,
    MarketAnalysisResponse, AgentInfoResponse
)
from .service import market_intelligence_service
from farmxpert.app.shared.utils import logger


router = APIRouter(
    prefix="/market-intelligence",
    tags=["Market Intelligence"]
)


@router.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint for Market Intelligence Agent"""
    return {
        "agent": "Market Intelligence Agent",
        "version": "2.0.0",
        "status": "active",
        "description": "Provides market analysis, price predictions, and farming recommendations"
    }


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    try:
        agent_info = market_intelligence_service.get_agent_info()
        return {
            "status": "healthy",
            "agent": agent_info["name"],
            "version": agent_info["version"],
            "capabilities": agent_info["capabilities"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/info", response_model=AgentInfoResponse)
async def get_agent_info():
    """Get agent information and capabilities"""
    try:
        agent_info = market_intelligence_service.get_agent_info()
        return AgentInfoResponse(**agent_info)
    except Exception as e:
        logger.error(f"Failed to get agent info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-analyze", response_model=MarketAnalysisResponse)
async def quick_analyze(request: QuickAnalysisRequest):
    """
    Quick market analysis endpoint
    
    Provides fast market analysis with basic parameters
    """
    try:
        logger.info(f"Quick analysis request: {request.crop} in {request.state}")
        
        # Run analysis
        result = await market_intelligence_service.quick_analyze(
            crop=request.crop,
            state=request.state,
            area_hectares=request.area_hectares,
            expected_yield_quintals_per_hectare=request.expected_yield_quintals_per_hectare,
            district=request.district
        )
        
        return MarketAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive-analyze", response_model=MarketAnalysisResponse)
async def comprehensive_analyze(request: ComprehensiveAnalysisRequest):
    """
    Comprehensive market analysis endpoint
    
    Provides detailed market analysis with full parameters
    """
    try:
        logger.info(f"Comprehensive analysis request: {request.crop_info.name} in {request.location.state}")
        
        # Convert to dictionaries
        crop_info = request.crop_info.model_dump(exclude_none=True)
        location = request.location.model_dump(exclude_none=True)
        farm_info = request.farm_info.model_dump(exclude_none=True)
        preferences = request.preferences.model_dump(exclude_none=True) if request.preferences else None
        
        # Run analysis
        result = await market_intelligence_service.comprehensive_analyze(
            crop_info=crop_info,
            location=location,
            farm_info=farm_info,
            preferences=preferences
        )
        
        return MarketAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{crop}/{state}")
async def analyze_crop_state(crop: str, state: str, area_hectares: float = None, 
                           expected_yield: float = None, district: str = None):
    """
    Simple analysis endpoint with path parameters
    
    Example: /analyze/cotton/Gujarat?area_hectares=10&expected_yield=15
    """
    try:
        logger.info(f"Path analysis request: {crop} in {state}")
        
        # Run analysis
        result = await market_intelligence_service.quick_analyze(
            crop=crop,
            state=state,
            area_hectares=area_hectares,
            expected_yield_quintals_per_hectare=expected_yield,
            district=district
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Path analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/markets/{state}")
async def get_markets_by_state(state: str, crop: str = None):
    """
    Get available markets for a state (optional crop filter)
    """
    try:
        # This would typically fetch from database or cache
        # For now, return basic state info
        return {
            "state": state,
            "crop_filter": crop,
            "message": "Market listing feature coming soon",
            "suggestion": f"Use /quick-analyze or /comprehensive-analyze for current market data"
        }
    except Exception as e:
        logger.error(f"Failed to get markets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crops")
async def get_supported_crops():
    """Get list of supported crops"""
    try:
        agent_info = market_intelligence_service.get_agent_info()
        return {
            "supported_crops": agent_info["supported_crops"],
            "total_crops": len(agent_info["supported_crops"])
        }
    except Exception as e:
        logger.error(f"Failed to get supported crops: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/states")
async def get_supported_states():
    """Get list of supported states"""
    try:
        agent_info = market_intelligence_service.get_agent_info()
        return {
            "supported_states": agent_info["supported_states"],
            "total_states": len(agent_info["supported_states"])
        }
    except Exception as e:
        logger.error(f"Failed to get supported states: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-gujarat-cotton")
async def test_gujarat_cotton():
    """
    Test endpoint for Gujarat cotton analysis
    """
    try:
        result = await market_intelligence_service.quick_analyze(
            crop="cotton",
            state="Gujarat",
            area_hectares=10,
            expected_yield_quintals_per_hectare=15,
            district="Ahmedabad"
        )
        
        return {
            "test_name": "Gujarat Cotton Analysis",
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
