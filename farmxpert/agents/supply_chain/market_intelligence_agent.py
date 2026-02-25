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
        """Get current market prices for crops"""
        prices = {}
        
        # Base prices by crop (per ton)
        base_prices = {
            "wheat": 2500,
            "maize": 1800,
            "rice": 3000,
            "pulses": 4500,
            "cotton": 6000,
            "sugarcane": 350,
            "soybeans": 4000,
            "sunflower": 3500
        }
        
        for crop in crops:
            base_price = base_prices.get(crop.lower(), 2000)
            current_price = base_price
            
            prices[crop] = {
                "current_price_per_ton": current_price,
                "price_trend": "stable",
                "market_volatility": "medium",
                "last_updated": datetime.now().isoformat()
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
