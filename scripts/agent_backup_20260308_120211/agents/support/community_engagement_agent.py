from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
from farmxpert.core.base_agent.base_agent import BaseAgent


class CommunityEngagementAgent(BaseAgent):
    name = "community_engagement_agent"
    description = "Facilitates peer networking, co-operative planning, shared purchases, or government interaction"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from farmxpert.tools.support.community_forum import CommunityForumTool
            self.forum_tool = CommunityForumTool()
        except ImportError:
            self.forum_tool = None
            # self.logger.warning("Could not import CommunityForumTool")

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide community engagement recommendations with LLM reasoning."""
        location = inputs.get("location", "unknown")
        farm_size = inputs.get("farm_size", 0)
        farmer_interests = inputs.get("farmer_interests", [])
        current_networks = inputs.get("current_networks", [])
        query = inputs.get("query", "")
        
        # Execute internal logic
        local_groups = self._find_local_groups(location)
        networking_opportunities = self._generate_networking_opportunities(
            location, farmer_interests, current_networks
        )
        cooperative_activities = self._suggest_cooperative_activities(farm_size, location)
        government_interaction = self._provide_government_interaction_guidance(location)
        
        # Tool integration
        forum_trends = []
        similar_issues = []
        
        if self.forum_tool:
            try:
                # Get trending topics
                forum_trends = self.forum_tool.get_trending_topics()
                # If there's a specific query, search for similar issues
                if query:
                    similar_issues = self.forum_tool.search_similar_issues(query)
            except Exception as e:
                pass

        # INJECT TOOL DATA INTO LLM CONTEXT
        inputs["additional_data"] = inputs.get("additional_data", {})
        inputs["additional_data"]["forum_trends"] = forum_trends
        inputs["additional_data"]["similar_issues"] = similar_issues
        inputs["additional_data"]["local_groups"] = local_groups
        inputs["additional_data"]["government_schemes"] = government_interaction

        return await self._handle_with_llm(inputs)
    
    def _find_local_groups(self, location: str) -> List[Dict[str, Any]]:
        """Find local farmer groups and organizations"""
        groups = [
            {
                "name": "Local Farmer Producer Organization",
                "type": "FPO",
                "members": 150,
                "activities": ["Bulk purchasing", "Collective marketing", "Training programs"],
                "contact": "fpo@local.com",
                "meeting_schedule": "Monthly",
                "benefits": ["Reduced input costs", "Better market access", "Knowledge sharing"]
            },
            {
                "name": "Agricultural Cooperative Society",
                "type": "Cooperative",
                "members": 200,
                "activities": ["Credit facilities", "Input supply", "Storage facilities"],
                "contact": "coop@agri.com",
                "meeting_schedule": "Bi-weekly",
                "benefits": ["Credit access", "Storage facilities", "Insurance schemes"]
            },
            {
                "name": "Organic Farmers Association",
                "type": "Association",
                "members": 75,
                "activities": ["Organic certification", "Market development", "Training"],
                "contact": "organic@farmers.com",
                "meeting_schedule": "Monthly",
                "benefits": ["Organic certification support", "Premium markets", "Technical guidance"]
            },
            {
                "name": "Women Farmers Collective",
                "type": "Collective",
                "members": 50,
                "activities": ["Skill development", "Micro-enterprises", "Support groups"],
                "contact": "women@farmers.com",
                "meeting_schedule": "Weekly",
                "benefits": ["Skill training", "Financial support", "Community support"]
            }
        ]
        
        return groups
    
    def _generate_networking_opportunities(self, location: str, interests: List[str], 
                                        current_networks: List[str]) -> List[Dict[str, Any]]:
        """Generate networking opportunities"""
        opportunities = [
            {
                "type": "Farmer Field Day",
                "description": "Visit successful farms in your area",
                "frequency": "Quarterly",
                "benefits": ["Learn best practices", "Network with successful farmers", "See new technologies"],
                "next_event": "Next month",
                "registration": "Free"
            },
            {
                "type": "Agricultural Exhibition",
                "description": "Annual agricultural fair and exhibition",
                "frequency": "Annual",
                "benefits": ["See latest technologies", "Meet suppliers", "Learn about new crops"],
                "next_event": "In 3 months",
                "registration": "₹500"
            },
            {
                "type": "Training Workshop",
                "description": "Skill development workshops",
                "frequency": "Monthly",
                "benefits": ["Learn new techniques", "Get certified", "Network with experts"],
                "next_event": "Next week",
                "registration": "₹1000"
            },
            {
                "type": "Market Visit",
                "description": "Visit wholesale markets",
                "frequency": "Monthly",
                "benefits": ["Understand market dynamics", "Meet traders", "Learn pricing"],
                "next_event": "Next month",
                "registration": "Free"
            }
        ]
        
        return opportunities
    
    def _suggest_cooperative_activities(self, farm_size: float, location: str) -> Dict[str, Any]:
        """Suggest cooperative activities"""
        activities = {
            "bulk_purchasing": {
                "description": "Collective purchase of inputs",
                "benefits": ["Reduced costs", "Better quality", "Bulk discounts"],
                "requirements": ["Minimum 10 farmers", "Advance payment", "Coordinated planning"],
                "estimated_savings": "15-25% on inputs"
            },
            "collective_marketing": {
                "description": "Joint marketing of produce",
                "benefits": ["Better prices", "Reduced transportation costs", "Market access"],
                "requirements": ["Quality standards", "Coordinated harvesting", "Market agreements"],
                "estimated_benefits": "20-30% higher prices"
            },
            "shared_equipment": {
                "description": "Sharing of farm equipment",
                "benefits": ["Reduced capital investment", "Better utilization", "Maintenance sharing"],
                "requirements": ["Equipment scheduling", "Maintenance agreements", "Cost sharing"],
                "estimated_savings": "40-60% on equipment costs"
            },
            "storage_facilities": {
                "description": "Shared storage and processing",
                "benefits": ["Better storage conditions", "Reduced losses", "Value addition"],
                "requirements": ["Storage space", "Processing equipment", "Management system"],
                "estimated_benefits": "Reduced post-harvest losses by 15-20%"
            }
        }
        
        return activities
    
    def _provide_government_interaction_guidance(self, location: str) -> Dict[str, Any]:
        """Provide guidance for government interaction"""
        guidance = {
            "government_schemes": [
                {
                    "name": "PM-KISAN",
                    "description": "Direct income support to farmers",
                    "amount": "₹6000 per year",
                    "eligibility": "All farmers",
                    "application": "Online through PM-KISAN portal"
                },
                {
                    "name": "PM-FASAL",
                    "description": "Crop insurance scheme",
                    "amount": "Subsidized premium",
                    "eligibility": "All farmers",
                    "application": "Through banks or insurance companies"
                },
                {
                    "name": "Kisan Credit Card",
                    "description": "Credit facility for farmers",
                    "amount": "Up to ₹3 lakh",
                    "eligibility": "All farmers",
                    "application": "Through banks"
                }
            ],
            "contact_information": {
                "agricultural_extension": "Local Krishi Vigyan Kendra",
                "banking": "Nearest bank branch",
                "insurance": "Local insurance office",
                "marketing": "APMC market office"
            },
            "application_process": {
                "step_1": "Visit local government office",
                "step_2": "Submit required documents",
                "step_3": "Follow up on application",
                "step_4": "Receive benefits"
            },
            "required_documents": [
                "Aadhaar card",
                "Land ownership documents",
                "Bank account details",
                "Crop insurance details",
                "Previous year records"
            ]
        }
        
        return guidance
    
    def _generate_recommendations(self, local_groups: List[Dict], 
                                networking_opportunities: List[Dict]) -> List[str]:
        """Generate community engagement recommendations"""
        recommendations = [
            "Join a local farmer group for collective benefits",
            "Participate in farmer field days to learn from others",
            "Attend agricultural exhibitions to stay updated",
            "Consider cooperative activities for cost savings",
            "Apply for government schemes for financial support"
        ]
        
        # Group-specific recommendations
        if local_groups:
            recommendations.extend([
                f"Join {local_groups[0]['name']} for {', '.join(local_groups[0]['benefits'][:2])}",
                "Participate in group meetings regularly",
                "Share your experiences with other members"
            ])
        
        # Networking recommendations
        if networking_opportunities:
            recommendations.extend([
                f"Attend the next {networking_opportunities[0]['type']}",
                "Prepare questions before attending events",
                "Follow up with contacts after events"
            ])
        
        return recommendations
