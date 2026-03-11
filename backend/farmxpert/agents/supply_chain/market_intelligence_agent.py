from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import MarketIntelligenceTool
from farmxpert.services.gemini_service import gemini_service


class MarketIntelligenceAgent(EnhancedBaseAgent):
    name = "market_intelligence_agent"
    description = "Provides insights into current and forecasted crop prices across different mandis and buyer channels"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "market_intelligence": MarketIntelligenceTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide market intelligence using mandi+global prices and trend charts"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        crops = context.get("crops", inputs.get("crops", []))
        location = context.get("farm_location", context.get("location", inputs.get("location", "unknown")))

        mandi = {}
        global_prices = {}
        charts = {}

        if "market_intelligence" in tools:
            try:
                mandi = await tools["market_intelligence"].fetch_mandi_prices(crops, location)
            except Exception as e:
                self.logger.warning(f"Failed to fetch mandi prices: {e}")
            
            try:
                global_prices = await tools["market_intelligence"].fetch_global_prices(crops)
            except Exception as e:
                self.logger.warning(f"Failed to fetch global prices: {e}")
                
            try:
                if mandi:
                    charts = await tools["market_intelligence"].plot_price_trend(mandi.get("mandi_prices", {}))
            except Exception as e:
                self.logger.warning(f"Failed to plot price trends: {e}")


        prompt = f"""
        You are a market intelligence advisor. Summarize current mandi prices, global indicators, and give sell recommendations.

        Query: "{query}"
        Location: {location}
        Crops: {crops}
        Mandi Snapshot: {json.dumps(mandi, indent=2)}
        Global Prices: {json.dumps(global_prices, indent=2)}
        Charts & Trends: {json.dumps(charts, indent=2)}

        Provide: current_prices, price_forecasts, market_trends, recommendations
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
                "charts": charts
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
