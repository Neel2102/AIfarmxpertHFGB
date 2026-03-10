"""
Base Agent Class for FarmXpert
Provides foundation for all specialized agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Base class for all FarmXpert agents
    """
    
    name: str = "base_agent"
    description: str = "Base agent for FarmXpert"
    
    @abstractmethod
    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle agent-specific logic
        Args:
            inputs: Input data for the agent
        Returns:
            Agent response data
        """
        pass
    
    def get_info(self) -> Dict[str, str]:
        """
        Get basic agent information
        Returns:
            Dictionary with agent name and description
        """
        return {
            "name": self.name,
            "description": self.description
        }
