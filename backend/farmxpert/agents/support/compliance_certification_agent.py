from __future__ import annotations
from typing import Dict, Any, List
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import ComplianceTool
from farmxpert.services.gemini_service import gemini_service


class ComplianceCertificationAgent(EnhancedBaseAgent):
    name = "compliance_certification_agent"
    description = "Guides the farmer through certification processes like organic, export standards, or government schemes"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = {
            "compliance": ComplianceTool()
        }

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide compliance and certification guidance using tools and LLM"""
        tools = self.tools
        context = inputs.get("context", inputs)
        query = inputs.get("query", "")

        certification_type = context.get("certification_type", inputs.get("certification_type", "organic"))
        farm_size = context.get("farm_size", inputs.get("farm_size", 0))
        current_practices = context.get("current_practices", inputs.get("current_practices", {}))
        location = context.get("location", inputs.get("location", "unknown"))
        
        status = {}
        requirements = {}
        roadmap = {}

        if "compliance" in tools:
            try:
                requirements = await tools["compliance"].get_certification_requirements(certification_type, location)
            except Exception as e:
                self.logger.warning(f"Failed to fetch requirements: {e}")
                
            try:
                status = await tools["compliance"].assess_compliance(certification_type, current_practices)
            except Exception as e:
                self.logger.warning(f"Failed to assess compliance: {e}")
                
            try:
                if status:
                    roadmap = await tools["compliance"].generate_roadmap(certification_type, status)
            except Exception as e:
                self.logger.warning(f"Failed to generate roadmap: {e}")

        prompt = f"""
        You are a certification and compliance expert. Given the context, provide a comprehensive path to obtaining "{certification_type}" certification.

        Query: "{query}"
        Location: {location}
        Farm Size: {farm_size} acres
        Current Practices: {json.dumps(current_practices)}
        
        Requirements fetched: {json.dumps(requirements, indent=2)}
        Compliance Assessment: {json.dumps(status, indent=2)}
        Proposed Roadmap: {json.dumps(roadmap, indent=2)}

        Provide: compliance_status, certification_requirements, compliance_roadmap, cost_analysis, documentation_guidance, recommendations
        """
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "compliance_certification"})

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "certification_type": certification_type,
                "location": location,
                "farm_size": farm_size,
                "current_practices": current_practices,
                "raw_requirements": requirements,
                "raw_status": status,
                "raw_roadmap": roadmap
            },
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
