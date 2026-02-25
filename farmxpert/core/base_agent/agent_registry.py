from __future__ import annotations
from typing import Dict, Type, Any, Optional, List
import sys
from pathlib import Path

try:
    # Make repo root importable so `import app.*` works when running from `farmxpert/`.
    _REPO_ROOT = Path(__file__).resolve().parents[3]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
except Exception:
    _REPO_ROOT = None
from .agent_interface import AgentInterface
from farmxpert.core.utils.logger import get_logger

try:
    from farmxpert.app.orchestrator.agent import OrchestratorAgent  # type: ignore
    APP_ORCHESTRATOR_AVAILABLE = True
except Exception:
    OrchestratorAgent = None
    APP_ORCHESTRATOR_AVAILABLE = False

# Import all agents
# Import all agents
from farmxpert.app.agents.crop_selector.agent import CropSelectorAgent
from farmxpert.app.agents.seed_selector.agent import SeedSelectionAgent
from farmxpert.agents.crop_planning.soil_health_agent import SoilHealthAgent
from farmxpert.agents.crop_planning.fertilizer_advisor_agent import FertilizerAdvisorAgent
from farmxpert.app.agents.irrigation_planner.agent import IrrigationPlannerAgent
from farmxpert.app.agents.pest_disease.agent import PestDiseaseDiagnosticAgent
from farmxpert.agents.crop_planning.weather_watcher_agent import WeatherWatcherAgent
from farmxpert.agents.crop_planning.growth_stage_monitor_agent import GrowthStageMonitorAgent

# Import farm operations agents
from farmxpert.agents.farm_operations.task_scheduler_agent import TaskSchedulerAgent
from farmxpert.agents.farm_operations.machinery_equipment_agent import MachineryEquipmentAgent
from farmxpert.agents.farm_operations.farm_layout_mapping_agent import FarmLayoutMappingAgent

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
from farmxpert.app.agents.farmer_coach.agent import FarmerCoachAgent
from farmxpert.app.agents.compliance.agent import ComplianceCertificationAgent
from farmxpert.agents.support.community_engagement_agent import CommunityEngagementAgent


class AppAgentAdapter:
    name: str
    description: str

    def __init__(self, app_strategy: str, name: str, description: str):
        self.name = name
        self.description = description
        self._app_strategy = app_strategy

    def _build_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        context = inputs.get("context") or {}
        request: Dict[str, Any] = {
            "query": inputs.get("query") or "",
            "strategy": self._app_strategy,
            "skip_llm_summary": True,
        }

        # Common normalized location fields
        location = context.get("location")
        if isinstance(location, dict):
            request["location"] = location

        # Common crop info fields
        crop_info: Dict[str, Any] = {}
        if isinstance(context.get("crop_info"), dict):
            crop_info.update(context["crop_info"])
        if isinstance(context.get("crop"), str) and context.get("crop"):
            crop_info.setdefault("name", context["crop"])
        if isinstance(context.get("growth_stage"), str) and context.get("growth_stage"):
            crop_info.setdefault("growth_stage", context["growth_stage"])
        if crop_info:
            request["crop_info"] = crop_info

        # Allow passthrough of dynamic data if caller already provides it
        for k in ("soil_data", "crop_data", "irrigation_data", "fertilizer_data", "resources"):
            if k in context:
                request[k] = context[k]

        return request

    def _extract_recommendations(self, agent_result: Any) -> List[str]:
        if not isinstance(agent_result, dict):
            return []
        data = agent_result.get("data") if isinstance(agent_result.get("data"), dict) else agent_result
        recs: List[str] = []

        # direct list
        if isinstance(data.get("recommendations"), list):
            recs.extend([str(x).strip() for x in data["recommendations"] if str(x).strip()])

        # soil health nested recommendations
        if isinstance(data.get("recommendations"), dict):
            for v in data["recommendations"].values():
                if isinstance(v, list):
                    recs.extend([str(x).strip() for x in v if str(x).strip()])

        # irrigation has recommendation string
        if isinstance(data.get("recommendation"), str) and data.get("recommendation").strip():
            recs.append(data["recommendation"].strip())

        # de-dupe + cap
        out: List[str] = []
        seen = set()
        for r in recs:
            if r in seen:
                continue
            seen.add(r)
            out.append(r)
            if len(out) >= 3:
                break
        return out

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not APP_ORCHESTRATOR_AVAILABLE or OrchestratorAgent is None:
            return {
                "success": False,
                "error": "App orchestrator not available",
                "recommendations": [],
                "warnings": ["Backend orchestration misconfiguration"],
                "next_steps": ["Check PYTHONPATH and app package imports"],
            }

        request = self._build_request(inputs)
        response = await OrchestratorAgent.handle_request(request)

        # Orchestrator returns: {success, agents_used, results, recommendations, ...}
        results = response.get("results") if isinstance(response, dict) else None
        agent_result = None
        if isinstance(results, dict):
            # strategy should route to single agent, but be defensive
            agent_result = next(iter(results.values()), None)

        recommendations = self._extract_recommendations(agent_result)

        return {
            "success": bool(response.get("success")) if isinstance(response, dict) else False,
            "data": agent_result.get("data") if isinstance(agent_result, dict) else agent_result,
            "recommendations": recommendations,
            "warnings": [],
            "next_steps": [],
            "meta": {
                "routing": response.get("routing") if isinstance(response, dict) else None,
                "agents_used": response.get("agents_used") if isinstance(response, dict) else None,
            },
        }


def _make_app_agent_class(agent_key: str, app_strategy: str, description: str):
    _agent_key = agent_key
    _app_strategy = app_strategy
    _description = description

    class _ConcreteAppAgentAdapter(AppAgentAdapter):
        name = _agent_key
        description = _description

        def __init__(self, **_kwargs):
            super().__init__(app_strategy=_app_strategy, name=_agent_key, description=_description)

    return _ConcreteAppAgentAdapter


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


