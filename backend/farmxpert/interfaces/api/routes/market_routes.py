"""
Market Intelligence Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from farmxpert.models.database import get_db
from farmxpert.models.user_models import User
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.agents.supply_chain.market_intelligence_agent import MarketIntelligenceAgent
from farmxpert.app.shared.utils import logger

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/prices")
async def get_market_prices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get market prices and advice for the user's specific crop and state."""
    try:
        # Determine crop and state
        crop = "Wheat"  # default
        state = "Unknown"
        
        # User is already current_user. We just need to check onboarding_data.
        profile = getattr(current_user, 'onboarding_data', {})
        if not isinstance(profile, dict):
            profile = {}

        if profile:
            if profile.get('specificCrop'):
                crop = profile.get('specificCrop')
            elif profile.get('mainCropCategory'):
                crop = profile.get('mainCropCategory')
            
            if profile.get('state'):
                state = profile.get('state')
                
        # Call Market Intelligence Agent
        agent = MarketIntelligenceAgent()
        
        # Prepare input for agent
        agent_input = {
            "query": f"What are the current market prices for {crop} in {state}?",
            "context": {
                "crops": [crop],
                "farm_location": state,
                "user_id": current_user.id
            }
        }
        
        result = await agent.handle(agent_input)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch market data")
            
        data = result.get("data", {})
        current_prices = data.get("current_prices", {}).get(crop, {})
        
        # Build the structured response for the dashboard
        dashboard_data = {
            "crop": crop,
            "state": state,
            "current_price": current_prices.get("current_price_per_ton", 0) / 10, # convert to per quintal
            "price_unit": "₹/quintal",
            "seven_day_trend": current_prices.get("trend_direction", "stable"),
            "trend_percent": current_prices.get("trend_percent", 0.0),
            "advice": current_prices.get("advice", "HOLD"),
            "advice_reason": current_prices.get("advice_reason", "Market is currently stable. Wait for better opportunities."),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching market prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching market prices: {str(e)}"
        )
