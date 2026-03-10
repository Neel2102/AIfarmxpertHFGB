from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from farmxpert.core.base_agent.base_agent import BaseAgent


class FarmerCoachAgent(BaseAgent):
    name = "farmer_coach_agent"
    description = "A conversational mentor that educates and supports the farmer with localized advice and seasonal tips"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide coaching and educational support to farmers"""
        farmer_query = inputs.get("query", "")
        context = inputs.get("context") or {}

        # Keep original imports pointing to the support package
        from farmxpert.agents.support.farmcoach_agent_pkg.agent.farmer_coach import (
            FarmerCoachAgent as _SchemeCoach,
        )
        from farmxpert.agents.support.farmcoach_agent_pkg.services.web_search_service import (
            WebSearchService as _WebSearchService,
        )
        from farmxpert.agents.support.farmcoach_agent_pkg.models.input_model import (
            FarmerQueryInput as _FarmerQueryInput,
        )

        svc = _WebSearchService()
        schemes = svc.search_schemes(farmer_query)

        language = context.get("language") or inputs.get("language") or "English"
        coach = _SchemeCoach()
        out = coach.process_query(
            _FarmerQueryInput(farmer_query=farmer_query, language=language, schemes_data=schemes)
        )

        data = out.model_dump() if hasattr(out, "model_dump") else out.dict()
        recs = []
        if isinstance(data, dict) and isinstance(data.get("schemes"), list):
            for s in data["schemes"][:3]:
                if isinstance(s, dict) and s.get("scheme_name"):
                    recs.append(f"Check eligibility for: {s['scheme_name']}")

        return {
            "agent": self.name,
            "success": True,
            "response": "Government scheme information based on your query.",
            "recommendations": recs,
            "warnings": [],
            "next_steps": ["Open the official scheme link and verify eligibility documents."],
            "data": data,
            "metadata": {"mode": "scheme_coach"},
        }
    
    def _generate_coaching_response(self, query: str, experience: str, location: str, 
                                  season: str, current_crops: List[str]) -> Dict[str, Any]:
        """Generate personalized coaching response"""
        response = {
            "answer": "",
            "confidence_level": "high",
            "personalized_advice": [],
            "common_mistakes_to_avoid": [],
            "success_stories": []
        }
        
        # Generate response based on query type
        if "crop selection" in query.lower():
            response["answer"] = f"Based on your location in {location} and the {season} season, I recommend focusing on crops that thrive in your region. Consider local market demand and your experience level."
            response["personalized_advice"].append("Start with crops you're familiar with and gradually experiment with new varieties")
            response["common_mistakes_to_avoid"].append("Avoid planting crops that don't suit your soil type or climate")
        
        elif "soil management" in query.lower():
            response["answer"] = "Soil health is the foundation of successful farming. Regular testing and organic amendments can significantly improve your yields."
            response["personalized_advice"].append("Test your soil every 2-3 years and maintain organic matter levels")
            response["common_mistakes_to_avoid"].append("Don't over-fertilize without soil testing")
        
        elif "pest management" in query.lower():
            response["answer"] = "Integrated pest management combines prevention, monitoring, and targeted treatment for sustainable pest control."
            response["personalized_advice"].append("Monitor your crops regularly and identify pests early")
            response["common_mistakes_to_avoid"].append("Avoid excessive pesticide use that can harm beneficial insects")
        
        elif "irrigation" in query.lower():
            response["answer"] = "Efficient irrigation is crucial for water conservation and optimal crop growth. Consider your soil type and crop water needs."
            response["personalized_advice"].append("Water early morning or evening to reduce evaporation")
            response["common_mistakes_to_avoid"].append("Don't over-water as it can lead to root diseases")
        
        else:
            response["answer"] = "I'm here to help you with any farming questions. Feel free to ask about crop selection, soil management, pest control, irrigation, or any other farming topic."
            response["personalized_advice"].append("Keep a farming journal to track what works best on your farm")
            response["common_mistakes_to_avoid"].append("Don't make major changes without testing on a small scale first")
        
        # Add experience-specific advice
        if experience == "beginner":
            response["personalized_advice"].extend([
                "Start with a small plot to learn and experiment",
                "Connect with local farmers for mentorship",
                "Attend agricultural extension programs"
            ])
        elif experience == "intermediate":
            response["personalized_advice"].extend([
                "Consider crop rotation for better soil health",
                "Explore precision agriculture techniques",
                "Build relationships with local markets"
            ])
        else:  # advanced
            response["personalized_advice"].extend([
                "Consider value-added processing for higher profits",
                "Explore organic certification opportunities",
                "Implement advanced monitoring systems"
            ])
        
        return response
    
    def _get_seasonal_tips(self, season: str, location: str, current_crops: List[str]) -> Dict[str, Any]:
        """Get seasonal farming tips"""
        seasonal_tips = {
            "general_tips": [],
            "crop_specific_tips": {},
            "weather_preparation": [],
            "market_opportunities": []
        }
        
        # Season-specific tips
        if season == "spring":
            seasonal_tips["general_tips"] = [
                "Prepare soil for planting season",
                "Start seed germination indoors for early crops",
                "Plan crop rotation for the year",
                "Check and repair irrigation systems"
            ]
            seasonal_tips["weather_preparation"] = [
                "Monitor for late frost warnings",
                "Prepare for spring rains",
                "Plan for temperature fluctuations"
            ]
        elif season == "summer":
            seasonal_tips["general_tips"] = [
                "Monitor soil moisture regularly",
                "Implement pest control measures",
                "Harvest early crops",
                "Prepare for monsoon season"
            ]
            seasonal_tips["weather_preparation"] = [
                "Prepare for heat stress on crops",
                "Plan for monsoon flooding",
                "Monitor for drought conditions"
            ]
        elif season == "autumn":
            seasonal_tips["general_tips"] = [
                "Harvest main crops",
                "Prepare soil for winter crops",
                "Store harvested produce properly",
                "Plan for next year's crops"
            ]
            seasonal_tips["weather_preparation"] = [
                "Prepare for cooler temperatures",
                "Plan for autumn rains",
                "Protect crops from early frost"
            ]
        elif season == "winter":
            seasonal_tips["general_tips"] = [
                "Plant winter crops",
                "Protect crops from frost",
                "Maintain soil health",
                "Plan for spring planting"
            ]
            seasonal_tips["weather_preparation"] = [
                "Prepare for frost protection",
                "Monitor for cold damage",
                "Plan for winter rains"
            ]
        
        # Crop-specific tips
        for crop in current_crops:
            if crop == "wheat":
                seasonal_tips["crop_specific_tips"]["wheat"] = [
                    "Monitor for rust diseases",
                    "Apply nitrogen at tillering stage",
                    "Control weeds early in the season"
                ]
            elif crop == "maize":
                seasonal_tips["crop_specific_tips"]["maize"] = [
                    "Monitor for corn borer",
                    "Apply irrigation during tasseling",
                    "Control weeds before canopy closure"
                ]
            elif crop == "rice":
                seasonal_tips["crop_specific_tips"]["rice"] = [
                    "Maintain proper water levels",
                    "Monitor for blast disease",
                    "Apply balanced fertilization"
                ]
        
        return seasonal_tips
    
    def _get_learning_resources(self, experience: str, query: str) -> Dict[str, Any]:
        """Get relevant learning resources"""
        resources = {
            "videos": [],
            "articles": [],
            "courses": [],
            "local_programs": [],
            "online_tools": []
        }
        
        # Experience-based resources
        if experience == "beginner":
            resources["courses"].extend([
                "Basic Farming Fundamentals",
                "Soil Management for Beginners",
                "Crop Planning 101"
            ])
            resources["videos"].extend([
                "How to Start Your First Farm",
                "Understanding Soil Types",
                "Basic Irrigation Techniques"
            ])
        elif experience == "intermediate":
            resources["courses"].extend([
                "Advanced Crop Management",
                "Integrated Pest Management",
                "Precision Agriculture Basics"
            ])
            resources["articles"].extend([
                "Crop Rotation Strategies",
                "Organic Farming Methods",
                "Market Analysis for Farmers"
            ])
        else:  # advanced
            resources["courses"].extend([
                "Sustainable Agriculture Systems",
                "Agricultural Technology Integration",
                "Farm Business Management"
            ])
            resources["online_tools"].extend([
                "Precision Agriculture Software",
                "Crop Modeling Tools",
                "Market Analysis Platforms"
            ])
        
        # Query-specific resources
        if "soil" in query.lower():
            resources["articles"].append("Understanding Soil Health Indicators")
            resources["videos"].append("Soil Testing and Amendment")
        elif "pest" in query.lower():
            resources["articles"].append("Integrated Pest Management Guide")
            resources["videos"].append("Natural Pest Control Methods")
        elif "irrigation" in query.lower():
            resources["articles"].append("Efficient Irrigation Systems")
            resources["videos"].append("Drip Irrigation Setup")
        
        return resources
    
    def _create_action_plan(self, query: str, experience: str) -> Dict[str, Any]:
        """Create actionable plan for the farmer"""
        action_plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "milestones": [],
            "success_metrics": []
        }
        
        # Immediate actions based on query
        if "crop selection" in query.lower():
            action_plan["immediate_actions"].extend([
                "Research local crop varieties",
                "Check soil conditions",
                "Analyze market demand",
                "Calculate input costs"
            ])
        elif "soil management" in query.lower():
            action_plan["immediate_actions"].extend([
                "Schedule soil testing",
                "Identify soil type",
                "Plan organic amendments",
                "Design crop rotation"
            ])
        elif "pest management" in query.lower():
            action_plan["immediate_actions"].extend([
                "Identify pest types",
                "Monitor pest populations",
                "Research control methods",
                "Plan integrated approach"
            ])
        
        # Experience-based goals
        if experience == "beginner":
            action_plan["short_term_goals"] = [
                "Establish basic farming practices",
                "Learn crop-specific requirements",
                "Build local farmer network",
                "Track farming activities"
            ]
            action_plan["long_term_goals"] = [
                "Achieve consistent yields",
                "Develop sustainable practices",
                "Build market relationships",
                "Improve soil health"
            ]
        elif experience == "intermediate":
            action_plan["short_term_goals"] = [
                "Optimize crop yields",
                "Implement crop rotation",
                "Improve pest management",
                "Enhance irrigation efficiency"
            ]
            action_plan["long_term_goals"] = [
                "Achieve organic certification",
                "Implement precision agriculture",
                "Develop value-added products",
                "Expand market reach"
            ]
        else:  # advanced
            action_plan["short_term_goals"] = [
                "Implement advanced technologies",
                "Optimize resource efficiency",
                "Develop niche markets",
                "Mentor other farmers"
            ]
            action_plan["long_term_goals"] = [
                "Establish sustainable farming system",
                "Create agricultural enterprise",
                "Contribute to agricultural innovation",
                "Build legacy for next generation"
            ]
        
        # Success metrics
        action_plan["success_metrics"] = [
            "Increased crop yields",
            "Reduced input costs",
            "Improved soil health",
            "Better market prices",
            "Enhanced knowledge and skills"
        ]
        
        return action_plan
    
    def _provide_encouragement(self, experience: str) -> List[str]:
        """Provide encouraging messages"""
        encouragement = []
        
        if experience == "beginner":
            encouragement.extend([
                "Every expert was once a beginner - you're on the right path!",
                "Small steps lead to big changes in farming",
                "Your willingness to learn is your greatest asset",
                "Every season brings new opportunities to grow"
            ])
        elif experience == "intermediate":
            encouragement.extend([
                "Your experience is valuable - keep building on it",
                "You're developing the skills of a master farmer",
                "Your farm is a testament to your dedication",
                "Continue learning and experimenting - it pays off"
            ])
        else:  # advanced
            encouragement.extend([
                "Your expertise is inspiring the next generation of farmers",
                "You're a leader in sustainable agriculture",
                "Your farm is a model of excellence",
                "Your knowledge is helping others succeed"
            ])
        
        return encouragement
    
    def _suggest_next_steps(self, query: str, experience: str) -> List[str]:
        """Suggest next steps for the farmer"""
        next_steps = []
        
        # General next steps
        next_steps.extend([
            "Implement one new practice this season",
            "Connect with local agricultural extension",
            "Join a farmer's group or cooperative",
            "Keep a detailed farming journal"
        ])
        
        # Query-specific next steps
        if "crop selection" in query.lower():
            next_steps.extend([
                "Visit local markets to understand demand",
                "Talk to neighboring farmers about their crops",
                "Research crop varieties suitable for your region"
            ])
        elif "soil management" in query.lower():
            next_steps.extend([
                "Schedule a soil test with local lab",
                "Start composting kitchen and farm waste",
                "Plan crop rotation for next season"
            ])
        elif "pest management" in query.lower():
            next_steps.extend([
                "Learn to identify common pests in your area",
                "Research natural pest control methods",
                "Monitor your crops regularly for early detection"
            ])
        
        return next_steps
