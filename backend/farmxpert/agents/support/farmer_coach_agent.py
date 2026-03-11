from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import FarmerCoachTool
from farmxpert.services.gemini_service import gemini_service


class FarmerCoachAgent(EnhancedBaseAgent):
    name = "farmer_coach_agent"
    description = "A conversational mentor that educates and supports the farmer with localized advice and seasonal tips"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "coach": FarmerCoachTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide coaching and educational support using tools and LLM"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        experience = context.get("experience", inputs.get("experience", "beginner"))
        location = context.get("location", inputs.get("location", "unknown"))
        season = context.get("season", inputs.get("season", "current"))
        current_crops = context.get("current_crops", inputs.get("current_crops", []))
        
        seasonal_tips = {}
        learning_resources = {}
        action_plan = {}

        if "coach" in tools:
            try:
                seasonal_tips = await tools["coach"].get_seasonal_tips(season, location, current_crops)
            except Exception as e:
                self.logger.warning(f"Failed to fetch seasonal tips: {e}")
                
            try:
                learning_resources = await tools["coach"].get_learning_resources(experience, query)
            except Exception as e:
                self.logger.warning(f"Failed to fetch learning resources: {e}")
                
            try:
                action_plan = await tools["coach"].create_action_plan(query, experience)
            except Exception as e:
                self.logger.warning(f"Failed to create action plan: {e}")

        prompt = f"""
        You are a supportive and knowledgeable farmer coach. Give personalized coaching based on the user's situation.
        Provide encouragement, answer their question, and structure the data collected from tools.

        Query: "{query}"
        Experience Level: {experience}
        Location: {location}
        Season: {season}
        Current Crops: {current_crops}
        
        Seasonal Tips found: {json.dumps(seasonal_tips, indent=2)}
        Learning Resources found: {json.dumps(learning_resources, indent=2)}
        Proposed Action Plan: {json.dumps(action_plan, indent=2)}

        Provide: coaching_response (encouragement, personalized_advice, common_mistakes), seasonal_tips, learning_resources, action_plan, next_steps
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "farmer_coach"})

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "experience": experience,
                "location": location,
                "season": season,
                "current_crops": current_crops,
                "raw_seasonal_tips": seasonal_tips,
                "raw_learning_resources": learning_resources,
                "raw_action_plan": action_plan
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
