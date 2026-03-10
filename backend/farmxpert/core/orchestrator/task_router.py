from __future__ import annotations
from typing import List, Dict, Any
import yaml
import os


class TaskRouter:
    def __init__(self):
        self.config_path = "config/agent_configs/orchestrator_config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to default plan
            return {
                "default_plan": [{"agent": "crop_selector_agent"}],
                "workflow_templates": {}
            }
    
    def plan(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Determine workflow based on query keywords
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["plant", "crop", "grow", "sow", "seed"]):
            workflow = "crop_planning"
        elif any(word in query_lower for word in ["schedule", "task", "operation", "work"]):
            workflow = "farm_operations"
        elif any(word in query_lower for word in ["harvest", "yield", "profit", "market"]):
            workflow = "harvest_planning"
        elif any(word in query_lower for word in ["insurance", "risk", "pest", "disease"]):
            workflow = "risk_management"
        elif any(word in query_lower for word in ["help", "learn", "certification", "community"]):
            workflow = "farmer_support"
        else:
            # Use default plan
            agent_names = self.config.get("default_plan", ["crop_selector_agent"])
            return [{"agent": agent, "inputs": context} for agent in agent_names]
        
        # Get workflow template
        workflow_templates = self.config.get("workflow_templates", {})
        agent_names = workflow_templates.get(workflow, self.config.get("default_plan", ["crop_selector_agent"]))
        
        return [{"agent": agent, "inputs": context} for agent in agent_names]


