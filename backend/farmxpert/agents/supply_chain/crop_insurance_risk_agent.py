from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import CropInsuranceTool
from farmxpert.services.gemini_service import gemini_service


class CropInsuranceRiskAgent(EnhancedBaseAgent):
    name = "crop_insurance_risk_agent"
    description = "Guides farmers on suitable insurance plans and provides claim process assistance in case of loss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "crop_insurance": CropInsuranceTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide crop insurance and risk management recommendations"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        crops = context.get("crops", inputs.get("crops", []))
        farm_size = context.get("farm_size", inputs.get("farm_size", 0))
        location = context.get("location", inputs.get("location", "unknown"))
        risk_factors = context.get("risk_factors", inputs.get("risk_factors", []))
        current_insurance = context.get("current_insurance", inputs.get("current_insurance", {}))
        
        # Tool-driven data fetching
        risk_assessment = {}
        insurance_plans = {}
        premium_estimates = {}

        if "crop_insurance" in tools:
            try:
                risk_assessment = await tools["crop_insurance"].assess_risk(crops, location, risk_factors)
            except Exception as e:
                self.logger.warning(f"Failed to assess risk: {e}")

            try:
                insurance_plans = await tools["crop_insurance"].fetch_insurance_plans(crops, location)
            except Exception as e:
                self.logger.warning(f"Failed to fetch insurance plans: {e}")

            try:
                premium_estimates = await tools["crop_insurance"].calculate_premium_estimates(farm_size, insurance_plans)
            except Exception as e:
                self.logger.warning(f"Failed to calculate premiums: {e}")

        prompt = f"""
        You are a crop insurance advisor. Based on the following data, provide actionable insurance recommendations.

        Query: "{query}"
        Location: {location}
        Crops: {crops}
        Farm Size: {farm_size} acres
        Risk Assessment: {json.dumps(risk_assessment, indent=2)}
        Plans: {json.dumps(insurance_plans, indent=2)}
        Premiums: {json.dumps(premium_estimates, indent=2)}
        Current Insurance: {json.dumps(current_insurance, indent=2)}

        Provide: recommended_plans, coverage_gaps, premium_summary, claim_guidance, next_steps
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "insurance_advice"})

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "risk_assessment": risk_assessment,
                "insurance_plans": insurance_plans,
                "premium_estimates": premium_estimates
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
    
