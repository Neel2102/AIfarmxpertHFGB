"""
Market Intelligence Agent - Main Application Integration
Adapted for FarmXpert main project structure
"""

import asyncio
import warnings
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Suppress all warnings for this module
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

logger = logging.getLogger(__name__)

# Use Simulated Service (DB-backed) instead of static mocks
from .simulated_service import simulated_market_service

REAL_AGENT_AVAILABLE = True


class MarketIntelligenceService:
    """Service class for Market Intelligence Agent integration"""
    
    def __init__(self):
        """Initialize the Market Intelligence Service"""
        self.agent = simulated_market_service
        self.use_real_agent = True

    @staticmethod
    def _coerce_result_to_dict(result: Any) -> Optional[Dict[str, Any]]:
        """Best-effort conversion of agent result to a JSON-serializable dict."""
        if result is None:
            return None
        try:
            if hasattr(result, "to_dict") and callable(getattr(result, "to_dict")):
                return result.to_dict()
            if hasattr(result, "model_dump") and callable(getattr(result, "model_dump")):
                return result.model_dump()
            if hasattr(result, "dict") and callable(getattr(result, "dict")):
                return result.dict()
            if hasattr(result, "__dict__"):
                return dict(result.__dict__)
        except Exception:
            return None
        return None
    
    async def quick_analyze(self, crop: str, state: str, area_hectares: Optional[float] = None, 
                          expected_yield_quintals_per_hectare: Optional[float] = None,
                          district: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform quick market analysis
        """
        return await self.agent.quick_analyze(
            crop, state, area_hectares, expected_yield_quintals_per_hectare, district
        )
    
    async def comprehensive_analyze(self, crop_info: Dict[str, Any], location: Dict[str, Any],
                                   farm_info: Dict[str, Any], 
                                   preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis
        """
        return await self.agent.comprehensive_analyze(
            crop_info, location, farm_info, preferences
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        if self.use_real_agent:
            return self.agent.get_agent_info()
        else:
            return self.agent.get_agent_info()


# Singleton instance
market_intelligence_service = MarketIntelligenceService()
