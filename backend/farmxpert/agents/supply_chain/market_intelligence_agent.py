from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import MarketIntelligenceTool
from farmxpert.services.gemini_service import gemini_service


class MarketIntelligenceAgent(EnhancedBaseAgent):
    name = "market_intelligence_agent"
    description = "Provides insights into current and forecasted crop prices across different mandis and buyer channels"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide market intelligence using mandi+global prices and trend charts"""
        tools = inputs.get("tools", {})
        context = inputs.get("context", {})
        query = inputs.get("query", "")

        crops = context.get("crops", inputs.get("crops", []))
        location = context.get("farm_location", inputs.get("location", "unknown"))

        mandi = {}
        global_prices = {}
        charts = {}

        try:
            if "market_intelligence" in tools:
                mandi = await tools["market_intelligence"].fetch_mandi_prices(crops, location)
                global_prices = await tools["market_intelligence"].fetch_global_prices(crops)
                charts = await tools["market_intelligence"].plot_price_trend(mandi.get("mandi_prices", {}))
        except Exception as e:
            self.logger.warning(f"Market tools failed: {e}")

        # Fallback computations
        current_prices = self._get_current_prices(crops, location)
        price_forecasts = self._generate_price_forecasts(crops)
        market_trends = self._analyze_market_trends(crops)

        prompt = f"""
You are a market intelligence advisor. Summarize current mandi prices, global indicators, and give sell recommendations.

Query: "{query}"
Location: {location}
Mandi Snapshot: {json.dumps(mandi.get('latest_snapshot', {}), indent=2)}
Global Prices: {json.dumps(global_prices.get('global_prices', {}), indent=2)}
Charts: {json.dumps(charts.get('insights', {}), indent=2)}
Baselines: {json.dumps(current_prices, indent=2)}
Forecasts: {json.dumps(price_forecasts, indent=2)}
"""
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "market_intelligence"})

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "location": location,
                "crops": crops,
                "mandi": mandi,
                "global_prices": global_prices,
                "charts": charts,
                "current_prices": current_prices,
                "price_forecasts": price_forecasts,
                "market_trends": market_trends
            },
            "recommendations": self._generate_recommendations(crops, current_prices, price_forecasts),
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
    
    def _get_current_prices(self, crops: List[str], location: str) -> Dict[str, Dict[str, Any]]:
        """Get current market prices for crops, returning realistic APMC simulated data."""
        import random
        from datetime import datetime
        
        prices = {}
        
        # Base prices by crop (per quintal for APMC standard reporting)
        base_prices = {
            "wheat": 2500,
            "maize": 1800,
            "rice": 3000,
            "pulses": 4500,
            "cotton": 6200,
            "sugarcane": 350,
            "soybeans": 4100,
            "sunflower": 5500,
            "groundnut": 6300,
            "chickpea": 5800,
        }
        
        # Use date to create pseudo-random but deterministic daily prices
        # so the numbers don't jump around on every refresh today
        today_seed = datetime.now().toordinal()
        
        for crop in crops:
            crop_lower = crop.lower()
            base_price = base_prices.get(crop_lower, 3500)
            
            # Seed random generator with crop + location + date constraint
            random.seed(f"{crop_lower}_{location.lower()}_{today_seed}")
            
            # Fluctuate up to 8% from base
            fluctuation_pct = random.uniform(-0.08, 0.08)
            current_price = int(base_price * (1 + fluctuation_pct))
            
            # Determine 7-day trend (compare to a pseudo-past price)
            past_fluctuation_pct = random.uniform(-0.05, 0.05)
            past_price = int(current_price * (1 + past_fluctuation_pct))
            
            trend_percent = ((current_price - past_price) / past_price) * 100
            trend_direction = "up" if trend_percent > 0 else "down" if trend_percent < 0 else "stable"
            
            if trend_percent > 5.0:
                advice = "SELL"
                reason = "Prices have surged recently. Capitalize on the current peak."
            elif trend_percent > 2.0:
                advice = "HOLD"
                reason = "Prices are rising. Wait 3-5 days for better returns."
            elif trend_percent < -3.0:
                advice = "HOLD"
                reason = "Market is currently down. Delay selling until prices recover."
            else:
                advice = "SELL"
                reason = "Prices are stable. Good time to sell if you need liquidity."
            
            prices[crop] = {
                # We return it conceptually as per quintal, since our routes scale it down from tons
                "current_price_per_ton": current_price * 10,  # simulate ton price for backwards compatibility
                "price_trend": trend_direction,
                "trend_direction": trend_direction,
                "trend_percent": round(trend_percent, 1),
                "advice": advice,
                "advice_reason": reason,
                "market_volatility": "medium",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        return prices
    
    def _generate_price_forecasts(self, crops: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate price forecasts for the next 6 months"""
        forecasts = {}
        
        for crop in crops:
            current_price = self._get_current_prices([crop], "unknown")[crop]["current_price_per_ton"]
            
            # Simple forecast with seasonal adjustment
            seasonal_adjustment = 1.05  # 5% increase
            forecast_price = current_price * seasonal_adjustment
            
            forecasts[crop] = {
                "forecast_price": round(forecast_price, 2),
                "confidence_level": "medium",
                "forecast_period": "6 months"
            }
        
        return forecasts
    
    def _analyze_market_trends(self, crops: List[str]) -> Dict[str, Any]:
        """Analyze market trends and patterns"""
        trends = {
            "overall_market_trend": "stable",
            "crop_specific_trends": {},
            "market_sentiment": "neutral"
        }
        
        for crop in crops:
            trends["crop_specific_trends"][crop] = {
                "trend": "stable",
                "strength": "medium"
            }
        
        return trends
    
    def _generate_recommendations(self, crops: List[str], current_prices: Dict, price_forecasts: Dict) -> List[str]:
        """Generate market recommendations for farmers"""
        recommendations = [
            "Monitor government procurement announcements for MSP updates",
            "Track export demand for better price opportunities",
            "Consider forward contracts for price stability",
            "Diversify selling across multiple markets to reduce risk"
        ]
        
        return recommendations
