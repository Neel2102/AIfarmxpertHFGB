from __future__ import annotations
from typing import Dict, Type, Any, Optional, List
from .agent_interface import AgentInterface
from farmxpert.core.utils.logger import get_logger

# Import all agents
# Import all agents
from farmxpert.agents.agronomy.app_agents.crop_selector.agent import CropSelectorAgent
from farmxpert.agents.agronomy.app_agents.seed_selector.agent import SeedSelectionAgent
from farmxpert.agents.agronomy.soil_health_agent import SoilHealthAgent
from farmxpert.agents.agronomy.fertilizer_advisor_agent import FertilizerAdvisorAgent
from farmxpert.agents.agronomy.app_agents.irrigation_planner.agent import IrrigationPlannerAgent
from farmxpert.agents.agronomy.app_agents.pest_disease.agent import PestDiseaseDiagnosticAgent
from farmxpert.agents.agronomy.weather_watcher_agent import WeatherWatcherAgent
from farmxpert.agents.agronomy.growth_stage_monitor_agent import GrowthStageMonitorAgent

# Import farm operations agents
from farmxpert.agents.operations.task_scheduler_agent import TaskSchedulerAgent
from farmxpert.agents.operations.machinery_equipment_agent import MachineryEquipmentAgent
from farmxpert.agents.operations.farm_layout_mapping_agent import FarmLayoutMappingAgent

# Import analytics agents
from farmxpert.agents.analytics.yield_predictor_agent import YieldPredictorAgent
from farmxpert.agents.analytics.profit_optimization_agent import ProfitOptimizationAgent
from farmxpert.agents.analytics.carbon_sustainability_agent import CarbonSustainabilityAgent

# Import supply chain agents
from farmxpert.agents.supply_chain.market_intelligence_agent import MarketIntelligenceAgent
from farmxpert.agents.supply_chain.logistics_storage_agent import LogisticsStorageAgent
from farmxpert.agents.supply_chain.input_procurement_agent import InputProcurementAgent
from farmxpert.agents.supply_chain.crop_insurance_risk_agent import CropInsuranceRiskAgent

# Import support agents
from farmxpert.agents.support.app_agents.farmer_coach.agent import FarmerCoachAgent
from farmxpert.agents.support.app_agents.compliance.agent import ComplianceCertificationAgent
from farmxpert.agents.support.community_engagement_agent import CommunityEngagementAgent


class AgentRegistry:
    """Registry for all available agents"""
    
    def __init__(self):
        self.logger = get_logger("agent_registry")
        self._agents: Dict[str, Type[AgentInterface]] = {}
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register all default agents"""
        # Crop Planning Agents
        self.register("crop_selector", CropSelectorAgent)
        self.register("seed_selection", SeedSelectionAgent)
        self.register("soil_health", SoilHealthAgent)
        self.register("fertilizer_advisor", FertilizerAdvisorAgent)
        self.register("irrigation_planner", IrrigationPlannerAgent)
        self.register("pest_disease_diagnostic", PestDiseaseDiagnosticAgent)
        self.register("weather_watcher", WeatherWatcherAgent)
        self.register("growth_stage_monitor", GrowthStageMonitorAgent)
        
        # Farm Operations Agents
        self.register("task_scheduler", TaskSchedulerAgent)
        self.register("machinery_equipment", MachineryEquipmentAgent)
        self.register("farm_layout_mapping", FarmLayoutMappingAgent)
        
        # Analytics Agents
        self.register("yield_predictor", YieldPredictorAgent)
        self.register("profit_optimization", ProfitOptimizationAgent)
        self.register("carbon_sustainability", CarbonSustainabilityAgent)
        
        # Supply Chain Agents
        self.register("market_intelligence", MarketIntelligenceAgent)
        self.register("logistics_storage", LogisticsStorageAgent)
        self.register("input_procurement", InputProcurementAgent)
        self.register("crop_insurance_risk", CropInsuranceRiskAgent)
        
        # Support Agents
        self.register("farmer_coach", FarmerCoachAgent)
        self.register("compliance_certification", ComplianceCertificationAgent)
        self.register("community_engagement", CommunityEngagementAgent)
    
    def register(self, name: str, agent_class: Type[AgentInterface]):
        """Register a new agent"""
        self._agents[name] = agent_class
        self.logger.info("agent_registered", name=name)
    
    def get_agent_class(self, name: str) -> Type[AgentInterface]:
        """Get agent class by name"""
        if name not in self._agents:
            raise ValueError(f"Unknown agent: {name}")
        return self._agents[name]
    
    def create_agent(self, name: str, **kwargs) -> AgentInterface:
        """Create an agent instance"""
        agent_class = self.get_agent_class(name)
        return agent_class(**kwargs)
    
    def list_agents(self) -> Dict[str, str]:
        """List all available agents with their descriptions"""
        return {
            name: agent_class.description 
            for name, agent_class in self._agents.items()
        }


# Global registry instance
_registry = AgentRegistry()


def create_agent(name: str, **kwargs) -> AgentInterface:
    """Factory function to create agents"""
    return _registry.create_agent(name, **kwargs)


def get_agent_class(name: str) -> Type[AgentInterface]:
    """Get agent class by name"""
    return _registry.get_agent_class(name)


def list_agents() -> Dict[str, str]:
    """List all available agents"""
    return _registry.list_agents()


