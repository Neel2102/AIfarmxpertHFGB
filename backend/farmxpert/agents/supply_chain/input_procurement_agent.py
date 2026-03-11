from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import InputProcurementTool
from farmxpert.services.gemini_service import gemini_service


class InputProcurementAgent(EnhancedBaseAgent):
    name = "input_procurement_agent"
    description = "Advises where and when to buy inputs like seeds, fertilizers, and agrochemicals — includes price comparison"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "input_procurement": InputProcurementTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide input procurement recommendations"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        required_inputs = context.get("required_inputs", inputs.get("required_inputs", []))
        farm_size = context.get("farm_size", inputs.get("farm_size", 0))
        budget = context.get("budget", inputs.get("budget", 0))
        location = context.get("location", inputs.get("location", "unknown"))
        season = context.get("season", inputs.get("season", "unknown"))
        
        suppliers = {}
        cost_estimates = {}
        budget_analysis = {}

        if "input_procurement" in tools:
            try:
                suppliers_res = await tools["input_procurement"].find_suppliers(required_inputs, location)
                suppliers = suppliers_res.get("available_suppliers", {})
            except Exception as e:
                self.logger.warning(f"Failed to find suppliers: {e}")

            try:
                cost_estimates = await tools["input_procurement"].estimate_costs(required_inputs, farm_size, suppliers)
            except Exception as e:
                self.logger.warning(f"Failed to estimate costs: {e}")

            try:
                budget_analysis = await tools["input_procurement"].analyze_budget(budget, cost_estimates)
            except Exception as e:
                self.logger.warning(f"Failed to analyze budget: {e}")

        prompt = f"""
        You are an agricultural procurement planner. Based on the following, provide an actionable procurement plan.

        Query: "{query}"
        Location: {location}
        Inputs Needed: {required_inputs}
        Farm Size: {farm_size} acres
        Budget: ${budget}
        Season: {season}
        Suppliers Found: {json.dumps(suppliers, indent=2)}
        Cost Estimates: {json.dumps(cost_estimates, indent=2)}
        Budget Analysis: {json.dumps(budget_analysis, indent=2)}

        Provide: recommended_suppliers, cost_breakdown, budget_status, procurement_timeline, final_recommendations
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "procurement_planning"})
        
        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "suppliers": suppliers,
                "cost_estimates": cost_estimates,
                "budget_analysis": budget_analysis
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
    
