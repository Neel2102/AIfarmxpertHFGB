from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.core.base_agent.output_schema import (
    StandardizedAgentOutput,
    AgentDecision,
    StructuredRecommendation,
    StructuredWarning,
    create_agent_decision,
    create_structured_recommendation,
    create_structured_warning
)
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
        
        # Build structured recommendations from market data
        structured_recommendations: List[StructuredRecommendation] = []
        mandi_prices = mandi.get("mandi_prices", {}) if isinstance(mandi, dict) else {}
        
        # Add top market recommendations
        if mandi_prices:
            for i, (crop, price_data) in enumerate(list(mandi_prices.items())[:3]):
                if isinstance(price_data, dict):
                    structured_recommendations.append(create_structured_recommendation(
                        action=f"Monitor {crop} prices at mandi",
                        reason=f"Current: ₹{price_data.get('current', 'N/A')}/quintal. Trend: {price_data.get('trend', 'stable')}",
                        timeline="monitor daily",
                        priority=1 if i == 0 else 2,
                        category="market"
                    ))
        
        # Add global price recommendations
        if global_prices and isinstance(global_prices, dict):
            for i, (crop, price) in enumerate(list(global_prices.items())[:2]):
                structured_recommendations.append(create_structured_recommendation(
                    action=f"Track global {crop} prices",
                    reason=f"Global price: ${price}/ton. Compare with local mandi rates",
                    timeline="weekly review",
                    priority=2,
                    category="market"
                ))
        
        decision = create_agent_decision(
            summary=f"Market intelligence for {len(crops)} crops at {location}. {len(mandi_prices)} mandi prices, {len(global_prices)} global prices tracked.",
            details=response[:200] if len(response) > 200 else response,
            confidence=0.85 if mandi_prices else 0.6
        )
        
        return StandardizedAgentOutput(
            agent=self.name,
            success=True,
            decision=decision,
            recommendations=structured_recommendations,
            warnings=[],
            data={
                "location": location,
                "crops": crops,
                "mandi": mandi,
                "global_prices": global_prices,
                "charts": charts
            },
            metadata={"model": "gemini", "tools_used": list(tools.keys())}
        ).to_dict()
