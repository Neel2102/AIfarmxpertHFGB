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
from farmxpert.services.tools import CommunityEngagementTool
from farmxpert.services.gemini_service import gemini_service


class CommunityEngagementAgent(EnhancedBaseAgent):
    name = "community_engagement_agent"
    description = "Facilitates peer networking, co-operative planning, shared purchases, or government interaction"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "community": CommunityEngagementTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide community engagement recommendations with tools and LLM."""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        location = context.get("location", inputs.get("location", "unknown"))
        farm_size = context.get("farm_size", inputs.get("farm_size", 0))
        farmer_interests = context.get("farmer_interests", inputs.get("farmer_interests", []))
        
        local_groups = {}
        government_schemes = {}
        forum_trends = {}

        if "community" in tools:
            try:
                local_groups = await tools["community"].get_local_groups(location)
            except Exception as e:
                self.logger.warning(f"Failed to fetch local groups: {e}")
                
            try:
                government_schemes = await tools["community"].get_government_schemes(location, farm_size)
            except Exception as e:
                self.logger.warning(f"Failed to fetch government schemes: {e}")
                
            try:
                forum_trends = await tools["community"].get_forum_trends(farmer_interests)
            except Exception as e:
                self.logger.warning(f"Failed to fetch forum trends: {e}")

        prompt = f"""
        You are an agricultural community organizer. Given the user's focus, suggest cooperative groups, events, and relevant government schemes.

        Query: "{query}"
        Location: {location}
        Farm Size: {farm_size} acres
        Interests: {farmer_interests}
        
        Local Groups Found: {json.dumps(local_groups, indent=2)}
        Government Schemes: {json.dumps(government_schemes, indent=2)}
        Forum Trends & Events: {json.dumps(forum_trends, indent=2)}

        Provide: local_groups, networking_opportunities, cooperative_activities, government_interaction, recommendations
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "community_engagement"})
        
        # Build structured recommendations from community data
        structured_recommendations: List[StructuredRecommendation] = []
        groups = local_groups if isinstance(local_groups, list) else []
        schemes = government_schemes if isinstance(government_schemes, list) else []
        
        # Add group recommendations
        for i, group in enumerate(groups[:3]):
            if isinstance(group, dict):
                structured_recommendations.append(create_structured_recommendation(
                    action=f"Join {group.get('name', 'Community Group')}",
                    reason=f"{group.get('type', 'Local group')} - {group.get('description', 'Community networking')}",
                    timeline="at your convenience",
                    priority=2,
                    category="community"
                ))
        
        # Add scheme recommendations
        for i, scheme in enumerate(schemes[:2]):
            if isinstance(scheme, dict):
                structured_recommendations.append(create_structured_recommendation(
                    action=f"Apply for {scheme.get('name', 'Government Scheme')}",
                    reason=f"Benefit: {scheme.get('benefit', 'Government support')}. Deadline: {scheme.get('deadline', 'Check locally')}",
                    timeline="before deadline",
                    priority=1 if i == 0 else 2,
                    category="government"
                ))
        
        decision = create_agent_decision(
            summary=f"Community engagement for {location}: {len(groups)} groups, {len(schemes)} schemes, {len(farmer_interests)} interests.",
            details=response[:200] if len(response) > 200 else response,
            confidence=0.75 if groups else 0.6
        )
        
        return StandardizedAgentOutput(
            agent=self.name,
            success=True,
            decision=decision,
            recommendations=structured_recommendations,
            warnings=[],
            data={
                "location": location,
                "farm_size": farm_size,
                "interests": farmer_interests,
                "raw_local_groups": local_groups,
                "raw_government_schemes": government_schemes,
                "raw_forum_trends": forum_trends
            },
            metadata={"model": "gemini", "tools_used": list(tools.keys())}
        ).to_dict()
