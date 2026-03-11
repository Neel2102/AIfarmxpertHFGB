from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import LogisticsStorageTool
from farmxpert.services.gemini_service import gemini_service


class LogisticsStorageAgent(EnhancedBaseAgent):
    name = "logistics_storage_agent"
    description = "Helps plan post-harvest activities: when to store, sell, or transport based on price windows and spoilage risks"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "logistics_storage": LogisticsStorageTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide logistics and storage recommendations"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        crops = context.get("crops", inputs.get("crops", []))
        harvest_quantity = context.get("harvest_quantity", inputs.get("harvest_quantity", {}))
        location = context.get("location", inputs.get("location", "unknown"))
        
        storage_facilities = {}
        logistics_routes = {}

        if "logistics_storage" in tools:
            try:
                storage_res = await tools["logistics_storage"].find_optimal_storage(crops, location, harvest_quantity)
                storage_facilities = storage_res.get("recommended_facilities", [])
            except Exception as e:
                self.logger.warning(f"Failed to find storage: {e}")

            if storage_facilities:
                # Extract destination names to pass to route planner
                destinations = [fac.get("name", "Unknown Facility") for fac in storage_facilities[:3]]
                try:
                    routes_res = await tools["logistics_storage"].route_logistics(location, destinations, "truck")
                    logistics_routes = routes_res.get("routes", [])
                except Exception as e:
                    self.logger.warning(f"Failed to calculate routes: {e}")

        prompt = f"""
        You are an agricultural logistics planning expert. Given the context, provide a comprehensive logistics and storage strategy.

        Query: "{query}"
        Location: {location}
        Crops: {crops}
        Harvest Quantities: {harvest_quantity} tons
        Optimal Storage Found: {json.dumps(storage_facilities, indent=2)}
        Logistics Routes: {json.dumps(logistics_routes, indent=2)}

        Provide: immediate_actions, storage_recommendations, transport_plan, risk_mitigation, final_recommendations
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "logistics_planning"})
        
        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "storage_facilities": storage_facilities,
                "logistics_routes": logistics_routes
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
