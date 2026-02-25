"""
Agent Configuration Service
Manages Indian agent names and configurations
"""

import yaml
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class AgentConfigService:
    """Service for managing agent configurations with Indian names"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "agent_configs" / "indian_agents.yaml"
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load agent configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            self._config = {"agents": {}, "categories": {}}
        except Exception as e:
            print(f"Error loading agent config: {e}")
            self._config = {"agents": {}, "categories": {}}
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent"""
        return self._config.get("agents", {}).get(agent_name)
    
    def get_indian_name(self, agent_name: str) -> str:
        """Get Indian name for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("indian_name", agent_name) if config else agent_name
    
    def get_full_name(self, agent_name: str) -> str:
        """Get full Indian name for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("full_name", agent_name) if config else agent_name
    
    def get_role(self, agent_name: str) -> str:
        """Get role description for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("role", "Agent") if config else "Agent"
    
    def get_description(self, agent_name: str) -> str:
        """Get description for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("description", "AI Agent") if config else "AI Agent"
    
    def get_avatar(self, agent_name: str) -> str:
        """Get avatar emoji for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("avatar", "🤖") if config else "🤖"
    
    def get_expertise(self, agent_name: str) -> List[str]:
        """Get expertise areas for an agent"""
        config = self.get_agent_config(agent_name)
        return config.get("expertise", []) if config else []
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent configurations"""
        return self._config.get("agents", {})
    
    def get_agents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get agents by category"""
        category_config = self._config.get("categories", {}).get(category, {})
        agent_names = category_config.get("agents", [])
        
        agents = []
        for agent_name in agent_names:
            # Find agent config by Indian name
            for agent_key, agent_config in self._config.get("agents", {}).items():
                if agent_config.get("indian_name") == agent_name:
                    agents.append({
                        "key": agent_key,
                        "indian_name": agent_name,
                        "full_name": agent_config.get("full_name", agent_name),
                        "role": agent_config.get("role", "Agent"),
                        "description": agent_config.get("description", "AI Agent"),
                        "avatar": agent_config.get("avatar", "🤖"),
                        "expertise": agent_config.get("expertise", [])
                    })
                    break
        
        return agents
    
    def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent categories"""
        return self._config.get("categories", {})
    
    def get_agent_by_indian_name(self, indian_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration by Indian name"""
        for agent_key, agent_config in self._config.get("agents", {}).items():
            if agent_config.get("indian_name") == indian_name:
                return {
                    "key": agent_key,
                    "indian_name": indian_name,
                    "full_name": agent_config.get("full_name", indian_name),
                    "role": agent_config.get("role", "Agent"),
                    "description": agent_config.get("description", "AI Agent"),
                    "avatar": agent_config.get("avatar", "🤖"),
                    "expertise": agent_config.get("expertise", [])
                }
        return None
    
    def get_agent_key_by_indian_name(self, indian_name: str) -> Optional[str]:
        """Get agent key by Indian name"""
        for agent_key, agent_config in self._config.get("agents", {}).items():
            if agent_config.get("indian_name") == indian_name:
                return agent_key
        return None
    
    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """Search agents by name, role, or expertise"""
        query = query.lower()
        results = []
        
        for agent_key, agent_config in self._config.get("agents", {}).items():
            # Search in various fields
            searchable_text = " ".join([
                agent_config.get("indian_name", ""),
                agent_config.get("full_name", ""),
                agent_config.get("role", ""),
                agent_config.get("description", ""),
                " ".join(agent_config.get("expertise", []))
            ]).lower()
            
            if query in searchable_text:
                results.append({
                    "key": agent_key,
                    "indian_name": agent_config.get("indian_name", agent_key),
                    "full_name": agent_config.get("full_name", agent_key),
                    "role": agent_config.get("role", "Agent"),
                    "description": agent_config.get("description", "AI Agent"),
                    "avatar": agent_config.get("avatar", "🤖"),
                    "expertise": agent_config.get("expertise", [])
                })
        
        return results
    
    def get_agent_display_info(self, agent_name: str) -> Dict[str, Any]:
        """Get complete display information for an agent"""
        config = self.get_agent_config(agent_name)
        if not config:
            return {
                "key": agent_name,
                "indian_name": agent_name,
                "full_name": agent_name,
                "role": "Agent",
                "description": "AI Agent",
                "avatar": "🤖",
                "expertise": [],
                "category": "general"
            }
        
        # Find category
        category = "general"
        for cat_key, cat_config in self._config.get("categories", {}).items():
            if config.get("indian_name") in cat_config.get("agents", []):
                category = cat_key
                break
        
        return {
            "key": agent_name,
            "indian_name": config.get("indian_name", agent_name),
            "full_name": config.get("full_name", agent_name),
            "role": config.get("role", "Agent"),
            "description": config.get("description", "AI Agent"),
            "avatar": config.get("avatar", "🤖"),
            "expertise": config.get("expertise", []),
            "category": category
        }

# Global instance
agent_config_service = AgentConfigService()
