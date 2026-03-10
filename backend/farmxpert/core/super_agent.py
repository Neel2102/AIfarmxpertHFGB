"""
Super Agent for FarmXpert
Orchestrates all agents and provides unified interface for user queries
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import re
from farmxpert.core.utils.logger import get_logger
from farmxpert.core.base_agent.agent_registry import AgentRegistry
from farmxpert.config.settings import settings
from farmxpert.services.gemini_service import gemini_service
from farmxpert.services.tools import SoilTool, WeatherTool, MarketTool, CropTool, FertilizerTool, PestDiseaseTool, IrrigationTool, WebScrapingTool, ClimatePredictionTool, MarketAnalysisTool, GeneticDatabaseTool, SoilSuitabilityTool, YieldPredictionTool, SoilSensorTool, AmendmentRecommendationTool, LabTestAnalyzerTool, FertilizerDatabaseTool, WeatherForecastTool, PlantGrowthSimulationTool, EvapotranspirationModelTool, IoTSoilMoistureTool, WeatherAPITool, ImageRecognitionTool, VoiceToTextTool, DiseasePredictionTool, WeatherMonitoringTool, AlertSystemTool, SatelliteImageProcessingTool, DroneImageProcessingTool, GrowthStagePredictionTool, TaskPrioritizationTool, RealTimeTrackingTool, MaintenanceTrackerTool, PredictiveMaintenanceTool, FieldMappingTool, YieldModelTool, ProfitOptimizationTool, MarketIntelligenceTool, LogisticsTool, ProcurementTool, InsuranceRiskTool, FarmerCoachTool, ComplianceCertificationTool, CommunityEngagementTool, CarbonSustainabilityTool
from farmxpert.core.super_agent_nl_formatter import format_response_as_natural_language, create_simple_greeting_response, is_simple_query

@dataclass
class AgentResponse:
    """Response from an individual agent"""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class SuperAgentResponse:
    """Final response from SuperAgent"""
    query: str
    success: bool
    response: Dict[str, Any]
    natural_language: str = ""  # Clean natural language response for UI
    agent_responses: List[AgentResponse] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    session_id: Optional[str] = None


class SuperAgent:
    """
    Super Agent that orchestrates all FarmXpert agents
    Uses Gemini to determine which agents to call and synthesizes responses
    """
    
    def __init__(self):
        self.logger = get_logger("super_agent")
        self.agent_registry = AgentRegistry()
        self.available_agents = self._get_available_agents()
        self.tools = {
            "soil": SoilTool(),
            "weather": WeatherTool(),
            "market": MarketTool(),
            "crop": CropTool(),
            "fertilizer": FertilizerTool(),
            "pest_disease": PestDiseaseTool(),
            "irrigation": IrrigationTool(),
            "web_scraping": WebScrapingTool(),
            "climate_prediction": ClimatePredictionTool(),
            "market_analysis": MarketAnalysisTool(),
            "genetic_database": GeneticDatabaseTool(),
            "soil_suitability": SoilSuitabilityTool(),
            "yield_prediction": YieldPredictionTool(),
            "soil_sensor": SoilSensorTool(),
            "amendment_recommendation": AmendmentRecommendationTool(),
            "lab_test_analyzer": LabTestAnalyzerTool(),
            "fertilizer_database": FertilizerDatabaseTool(),
            "weather_forecast": WeatherForecastTool(),
            "plant_growth_simulation": PlantGrowthSimulationTool(),
            "evapotranspiration_model": EvapotranspirationModelTool(),
            "iot_soil_moisture": IoTSoilMoistureTool(),
            "weather_api": WeatherAPITool(),
            "image_recognition": ImageRecognitionTool(),
            "voice_to_text": VoiceToTextTool(),
            "disease_prediction": DiseasePredictionTool(),
            "weather_monitoring": WeatherMonitoringTool(),
            "alert_system": AlertSystemTool(),
            "satellite_image_processing": SatelliteImageProcessingTool(),
            "drone_image_processing": DroneImageProcessingTool(),
            "growth_stage_prediction": GrowthStagePredictionTool(),
            "task_prioritization": TaskPrioritizationTool(),
            "real_time_tracking": RealTimeTrackingTool(),
            "maintenance_tracker": MaintenanceTrackerTool(),
            "predictive_maintenance": PredictiveMaintenanceTool(),
            "field_mapping": FieldMappingTool(),
            "yield_model": YieldModelTool(),
            "profit_optimization": ProfitOptimizationTool(),
            "market_intelligence": MarketIntelligenceTool(),
            "logistics": LogisticsTool(),
            "procurement": ProcurementTool(),
            "insurance_risk": InsuranceRiskTool(),
            "farmer_coach": FarmerCoachTool(),
            "compliance_cert": ComplianceCertificationTool(),
            "community": CommunityEngagementTool(),
            "carbon_sustainability": CarbonSustainabilityTool()
        }

    def _safe_list(self, items: List[str], max_items: int = 5) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items or []:
            if not item or not isinstance(item, str):
                continue
            if item in seen:
                continue
            if item not in self.available_agents:
                continue
            seen.add(item)
            out.append(item)
            if len(out) >= max_items:
                break
        return out

    def _get_strategy_from_context(self, context: Optional[Dict[str, Any]]) -> Optional[str]:
        if not context or not isinstance(context, dict):
            return None
        strategy = context.get("strategy")
        if not strategy and isinstance(context.get("routing"), dict):
            strategy = context["routing"].get("strategy")
        if not strategy:
            return None
        return str(strategy).strip().lower()

    def _select_agents_by_strategy(self, context: Optional[Dict[str, Any]]) -> Optional[List[str]]:
        strategy = self._get_strategy_from_context(context)
        if not strategy:
            return None
        mapping = {
            "weather": ["weather_watcher"],
            "weather_only": ["weather_watcher"],
            "growth": ["growth_stage_monitor"],
            "growth_only": ["growth_stage_monitor"],
            "irrigation": ["irrigation_planner"],
            "irrigation_only": ["irrigation_planner"],
            "fertilizer": ["fertilizer_advisor"],
            "fertilizer_only": ["fertilizer_advisor"],
            "soil": ["soil_health"],
            "soil_health": ["soil_health"],
            "soil_health_only": ["soil_health"],
            "market": ["market_intelligence"],
            "market_only": ["market_intelligence"],
            "tasks": ["task_scheduler"],
            "task_scheduler": ["task_scheduler"],
            "task_scheduling": ["task_scheduler"],
            "both": ["weather_watcher", "growth_stage_monitor"],
            "comprehensive": ["weather_watcher", "soil_health", "irrigation_planner", "fertilizer_advisor", "market_intelligence", "task_scheduler"],
            "comprehensive_analysis": ["weather_watcher", "soil_health", "irrigation_planner", "fertilizer_advisor", "market_intelligence", "task_scheduler"],
            "auto": None,
        }
        selected = mapping.get(strategy)
        if selected is None:
            return None
        return self._safe_list(selected)

    def _select_agents_by_payload(self, context: Optional[Dict[str, Any]]) -> Optional[List[str]]:
        if not context or not isinstance(context, dict):
            return None
        location = context.get("location") or {}
        crop = context.get("crop") or context.get("crop_data") or {}
        has_location = isinstance(location, dict) and (
            bool(location.get("latitude") and location.get("longitude"))
            or bool(location.get("lat") and location.get("lon"))
        )
        has_crop = bool(crop)
        if has_location and has_crop:
            return self._safe_list(["weather_watcher", "growth_stage_monitor", "irrigation_planner", "fertilizer_advisor", "soil_health"])
        if has_location:
            return self._safe_list(["weather_watcher"])
        if has_crop:
            return self._safe_list(["growth_stage_monitor", "soil_health"])
        return None

    def _select_agents_by_keywords(self, query: str) -> Optional[List[str]]:
        q = (query or "").lower()
        if not q:
            return None

        def has_any(keywords: List[str]) -> bool:
            return any(re.search(r"\b" + re.escape(k) + r"\b", q) for k in keywords)

        wants_seeds = has_any([
            "seed", "seeds", "variety", "varieties", "hybrid", "gmo"
        ])
        wants_crop_planning = has_any([
            "crop", "crops", "plant", "sow", "kharif", "rabi", "season"
        ])
        wants_weather = has_any([
             "weather", "rain", "rainfall", "temperature", "forecast", "humidity", "wind", "storm", "drought"
         ])
        wants_growth = has_any([
            "growth", "stage", "seedling", "vegetative", "flowering", "maturity", "harvest", "crop health", "plant health"
         ])
        wants_irrigation = has_any([
            "irrigation", "irrigate", "watering", "drip", "sprinkler", "pump"
        ])
        wants_fertilizer = has_any([
            "fertilizer", "nutrient", "npk", "urea", "dap", "mop", "compost", "manure"
        ])
        wants_soil = has_any([
            "soil", "ph", "salinity", "organic matter", "soil test"
        ])
        wants_pest = has_any([
            "pest", "disease", "fungus", "blight", "leaf spot", "insect", "spots", "yellow", "yellowing", "wilting", "curl", "mosaic", "rot"
         ])
        wants_market = has_any([
            "market", "price", "sell", "mandi", "apmc", "profit", "revenue"
        ])
        wants_tasks = has_any([
            "task", "schedule", "plan", "today", "tomorrow", "weekly", "daily", "reminder"
        ])
        wants_insurance = has_any([
            "insurance", "risk", "claim"
        ])

        wants_yield = has_any([
            "yield", "production", "quantity", "quintal", "ton"
        ])
        wants_profit = has_any([
            "profit", "loss", "margin", "income", "revenue", "cost", "expense", "budget"
        ])

        selected: List[str] = []
        if wants_crop_planning:
            selected.append("crop_selector")
        if wants_seeds:
             selected.append("seed_selection")
        if wants_weather:
            selected.append("weather_watcher")
        if wants_growth:
            selected.append("growth_stage_monitor")
        if wants_irrigation:
            selected.append("irrigation_planner")
        if wants_fertilizer:
            selected.append("fertilizer_advisor")
        if wants_soil:
            selected.append("soil_health")
        if wants_pest:
            selected.append("pest_disease_diagnostic")
        if wants_market:
            selected.append("market_intelligence")
        if wants_tasks:
            selected.append("task_scheduler")
        if wants_insurance:
            selected.append("crop_insurance_risk")
        if wants_yield:
            selected.append("yield_predictor")
        if wants_profit:
            selected.append("profit_optimization")

        selected = self._safe_list(selected)
        return selected or None

    async def _select_agents(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        # Check intent first to handle general conversation in streaming/direct mode
        intent = await self._classify_intent(query, context)
        if intent == "GENERAL_CONVERSATION":
            return ["__general_chat__"]

        strategy_selected = self._select_agents_by_strategy(context)
        if strategy_selected:
            return strategy_selected

        keyword_selected = self._select_agents_by_keywords(query)
        if keyword_selected:
            return keyword_selected

        payload_selected = self._select_agents_by_payload(context)
        if payload_selected:
            return payload_selected

        gemini_selected = await self._select_agents_with_gemini(query, context)
        gemini_selected = self._safe_list(gemini_selected)
        if gemini_selected:
            return gemini_selected

        return self._safe_list(["crop_selector", "farmer_coach"], max_items=2)

    def _get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available agents"""
        agents_info = {}
        
        # Crop Planning Agents
        agents_info.update({
            "crop_selector": {
                "name": "Crop Selector Agent",
                "description": "Helps select the best crops based on soil, weather, and market conditions",
                "category": "crop_planning",
                "tools": ["soil", "weather", "market", "crop", "web_scraping", "climate_prediction", "market_analysis"]
            },
            "seed_selection": {
                "name": "Seed Selection Agent", 
                "description": "Recommends the best seeds and varieties for selected crops",
                "category": "crop_planning",
                "tools": ["market", "genetic_database", "soil_suitability", "yield_prediction"]
            },
            "soil_health": {
                "name": "Soil Health Agent",
                "description": "Analyzes soil conditions and provides health recommendations",
                "category": "crop_planning", 
                "tools": ["soil", "crop", "soil_sensor", "amendment_recommendation", "lab_test_analyzer"]
            },
            "fertilizer_advisor": {
                "name": "Fertilizer Advisor Agent",
                "description": "Provides fertilizer recommendations based on soil analysis",
                "category": "crop_planning",
                "tools": ["soil", "fertilizer", "crop", "fertilizer_database", "weather_forecast", "plant_growth_simulation"]
            },
            "irrigation_planner": {
                "name": "Irrigation Planner Agent",
                "description": "Plans irrigation schedules based on weather and crop needs",
                "category": "crop_planning",
                "tools": ["weather", "irrigation", "crop", "evapotranspiration_model", "iot_soil_moisture", "weather_api"]
            },
            "pest_disease_diagnostic": {
                "name": "Pest & Disease Diagnostic Agent",
                "description": "Diagnoses pest and disease issues and provides treatment plans",
                "category": "crop_planning",
                "tools": ["pest_disease", "crop", "image_recognition", "voice_to_text", "disease_prediction"]
            },
            "weather_watcher": {
                "name": "Weather Watcher Agent",
                "description": "Monitors weather conditions and provides forecasts",
                "category": "crop_planning",
                "tools": ["weather", "crop", "weather_monitoring", "alert_system"]
            },
            "growth_stage_monitor": {
                "name": "Growth Stage Monitor Agent",
                "description": "Tracks crop growth stages and provides care recommendations",
                "category": "crop_planning",
                "tools": ["crop", "satellite_image_processing", "drone_image_processing", "growth_stage_prediction"]
            }
        })
        
        # Farm Operations Agents
        agents_info.update({
            "task_scheduler": {
                "name": "Task Scheduler Agent",
                "description": "Schedules farm tasks and operations efficiently",
                "category": "farm_operations",
                "tools": ["task_prioritization", "real_time_tracking", "weather_api"]
            },
            "machinery_equipment": {
                "name": "Machinery & Equipment Agent",
                "description": "Manages machinery and equipment recommendations",
                "category": "farm_operations",
                "tools": ["maintenance_tracker", "predictive_maintenance"]
            },
            "farm_layout_mapping": {
                "name": "Farm Layout Mapping Agent",
                "description": "Helps design and optimize farm layout",
                "category": "farm_operations",
                "tools": ["field_mapping"]
            }
        })
        
        # Analytics Agents
        agents_info.update({
            "yield_predictor": {
                "name": "Yield Predictor Agent",
                "description": "Predicts crop yields based on various factors",
                "category": "analytics",
                "tools": ["yield_model", "weather", "crop", "soil"]
            },
            "profit_optimization": {
                "name": "Profit Optimization Agent",
                "description": "Optimizes farm profitability through various strategies",
                "category": "analytics",
                "tools": ["profit_optimization", "market", "crop"]
            },
            "carbon_sustainability": {
                "name": "Carbon Sustainability Agent",
                "description": "Helps with carbon footprint and sustainability practices",
                "category": "analytics",
                "tools": ["carbon_sustainability"]
            }
        })
        
        # Supply Chain Agents
        agents_info.update({
            "market_intelligence": {
                "name": "Market Intelligence Agent",
                "description": "Provides market insights and price trends",
                "category": "supply_chain",
                "tools": ["market", "crop", "market_intelligence"]
            },
            "logistics_storage": {
                "name": "Logistics & Storage Agent",
                "description": "Manages logistics and storage recommendations",
                "category": "supply_chain",
                "tools": ["logistics", "market", "weather"]
            },
            "input_procurement": {
                "name": "Input Procurement Agent",
                "description": "Helps with procurement of farm inputs",
                "category": "supply_chain",
                "tools": ["procurement", "market"]
            },
            "crop_insurance_risk": {
                "name": "Crop Insurance & Risk Agent",
                "description": "Provides risk assessment and insurance recommendations",
                "category": "supply_chain",
                "tools": ["insurance_risk", "weather", "market"]
            }
        })
        
        # Support Agents
        agents_info.update({
            "farmer_coach": {
                "name": "Farmer Coach Agent",
                "description": "Provides coaching and educational support to farmers",
                "category": "support",
                "tools": ["farmer_coach"]
            },
            "compliance_certification": {
                "name": "Compliance & Certification Agent",
                "description": "Helps with regulatory compliance and certifications",
                "category": "support",
                "tools": ["compliance_cert"]
            },
            "community_engagement": {
                "name": "Community Engagement Agent",
                "description": "Facilitates community engagement and knowledge sharing",
                "category": "support",
                "tools": ["community"]
            }
        })
        
        return agents_info
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> SuperAgentResponse:
        """
        Main method to process user queries
        Uses Gemini to determine which agents to call and synthesizes responses
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(
                "Processing query",
                extra={
                    "query_preview": query[:100],
                    "session_id": session_id,
                    "context_keys": list(context.keys()) if context else [],
                    "timestamp": start_time.isoformat()
                }
            )
            
            # --- 0. INTELLIGENT ROUTING ---
            # Quickly classify if this is a general chat or specific advisory
            intent = await self._classify_intent(query, context)
            self.logger.info(f"Query Intent Classified: {intent}")

            if intent == "GENERAL_CONVERSATION":
                # Handle directly without sub-agents
                response_text = await self._handle_general_conversation(query, context)
                execution_time = (datetime.now() - start_time).total_seconds()
                return SuperAgentResponse(
                    query=query,
                    success=True,
                    response={"answer": response_text},
                    natural_language=response_text,
                    agent_responses=[],
                    execution_time=execution_time,
                    session_id=session_id
                )

            # --- 1. AGENT SELECTION (For specific/advisory queries) ---
            self.logger.debug("Starting agent selection")
            agent_selection = await self._select_agents(query, context)
            self.logger.info(
                "Agent selection completed",
                extra={
                    "selected_agents": agent_selection,
                    "agent_count": len(agent_selection)
                }
            )
            
            # --- 2. EXECUTE AGENTS ---
            self.logger.debug("Starting agent execution")
            agent_responses = await self._execute_agents(agent_selection, query, context)
            
            # Log agent execution results
            successful_agents = [r.agent_name for r in agent_responses if r.success]
            failed_agents = [r.agent_name for r in agent_responses if not r.success]
            
            self.logger.info(
                "Agent execution completed",
                extra={
                    "successful_agents": successful_agents,
                    "failed_agents": failed_agents,
                    "total_execution_time": sum(r.execution_time for r in agent_responses)
                }
            )
            
            # --- 3. SYNTHESIZE RESPONSE ---
            self.logger.debug("Starting response synthesis")
            final_response: Dict[str, Any] = await self._synthesize_response(query, agent_responses, context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                "Query processing completed successfully",
                extra={
                    "total_execution_time": execution_time,
                    "response_size": len(json.dumps(final_response, ensure_ascii=False)) if isinstance(final_response, dict) else len(str(final_response)),
                    "agents_used": len(agent_responses)
                }
            )
            
            # Format as natural language
            agent_names = [r.agent_name for r in agent_responses if r.success]
            natural_language = format_response_as_natural_language(
                query=query,
                response_data=final_response,
                agent_names=agent_names,
                context=context
            )
            
            return SuperAgentResponse(
                query=query,
                success=True,
                response=final_response,
                natural_language=natural_language,
                agent_responses=agent_responses,
                execution_time=execution_time,
                session_id=session_id
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                "Error processing query",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": execution_time,
                    "query_preview": query[:100]
                },
                exc_info=True
            )
            
            error_message = f"I apologize, but I encountered an error while processing your query: {str(e)}"
            
            return SuperAgentResponse(
                query=query,
                success=False,
                response={"answer": error_message},
                natural_language=error_message,
                execution_time=execution_time,
                session_id=session_id
            )
    
    async def _classify_intent(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Classify if query is GENERAL_CONVERSATION or SPECIFIC_ADVISORY"""
        # Simple heuristics for speed
        q_lower = query.lower().strip()

        # Handle follow-up questions (e.g., "why?", "how?", "when?") using conversation context.
        # If there is recent chat history, treat these as advisory follow-ups instead of general chat.
        if context and isinstance(context.get("chat_history"), list) and len(context.get("chat_history")) >= 2:
            if q_lower in {"why", "why?", "why?\\", "how", "how?", "when", "when?", "explain", "explain?"}:
                return "SPECIFIC_ADVISORY"
        
        # Greetings and simple questions (Regex for robustness)
        # Matches "hi", "hii", "hello", "hey", "hola", "namaste", "good morning", etc.
        greeting_pattern = r"^(hi+|hello|hey|hola|namaste|good\s*(morning|afternoon|evening)|greetings).{0,20}$"
        if re.match(greeting_pattern, q_lower):
            return "GENERAL_CONVERSATION"
            
        # Questions about identity
        if "who are you" in q_lower or "what can you do" in q_lower or ("help" in q_lower and len(q_lower) < 20):
            return "GENERAL_CONVERSATION"
            
        # Very short queries usually are conversational unless specific keywords
        if len(q_lower.split()) <= 2:
            # Check if it looks like a crop name or keyword
            keywords = ["yield", "pest", "disease", "price", "market", "weather", "soil", "farm", "crop", "sowing", "seed", "irrigation", "fertilizer"]
            if any(k in q_lower for k in keywords):
                return "SPECIFIC_ADVISORY"
            # If it's just a random short phrase not related to farming, treat as chat
            return "GENERAL_CONVERSATION"

        return "SPECIFIC_ADVISORY"

    async def _handle_general_conversation(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Handle general conversation directly using Gemini"""
        # Optimization: Instant response for simple greetings
        if is_simple_query(query):
            return create_simple_greeting_response(query)

        prompt = f"""
You are FarmXpert, a helpful agricultural AI assistant.
User Query: "{query}"

Answer the user directly and politely. Keep it brief. 
If they ask what you can do, explain that you are an expert system orchestrating multiple specialized agents for Soil, Weather, Market, and Crop analysis.
"""
        return await gemini_service.generate_response(prompt, {"task": "general_chat"})
    
    async def _select_agents_with_gemini(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Use Gemini to determine which agents should handle the query
        """
        # Create agent information for Gemini
        agents_info_text = self._format_agents_for_gemini()
        
        # Format chat history if available
        history_text = ""
        if context and "chat_history" in context and isinstance(context["chat_history"], list):
            history_items = []
            for item in context["chat_history"]:
                role = "Farmer" if item.get("role") == "user" else "Assistant"
                content = item.get("content", "")
                history_items.append(f"{role}: {content}")
            if history_items:
                history_text = "\nConversation History:\n" + "\n".join(history_items) + "\n"
        
        prompt = f"""
You are an AI coordinator for FarmXpert, an agricultural expert system. Your job is to analyze a farmer's query and determine which specialized agents should handle it.

Available Agents:
{agents_info_text}

{history_text}
Farmer's Query: "{query}"

Context: {context or "No additional context provided"}

Based on the query and conversation history, select the most relevant agents (1-5 agents maximum).
If the user asks a follow-up question (e.g., "what about for wheat?"), use the history to understand the full context.

Consider:
1. The main topic/domain of the query
1. The main topic/domain of the query
2. What information the farmer needs
3. Which agents can provide the most relevant expertise
4. Agent dependencies (some agents work better together)

Respond with a JSON array of agent names (use the exact agent keys from the list above):
["agent1", "agent2", "agent3"]

Only include agents that are directly relevant to answering the query. If the query is very specific, you might only need 1-2 agents. If it's complex, you might need 3-5 agents.

IMPORTANT: If a query is about a specific sub-domain like 'seeds', 'irrigation', 'pests', or 'fertilizer', MUST select the corresponding specialized agent (e.g., 'seed_selection', 'irrigation_planner', 'pest_disease_diagnostic') instead of the general 'crop_selector'.
"""
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "agent_selection"})
            
            # Parse the JSON response
            self.logger.info(f"Gemini routing response: {response}")
            agent_list = self._parse_agent_selection(response)
            self.logger.info(f"Parsed agent list: {agent_list}")
            
            # Validate that selected agents exist
            valid_agents = [agent for agent in agent_list if agent in self.available_agents]
            
            if not valid_agents:
                # Fallback to a default set of agents
                valid_agents = ["crop_selector", "farmer_coach"]
            
            self.logger.info(f"Selected agents: {valid_agents}")
            return valid_agents
            
        except Exception as e:
            self.logger.error(f"Error in agent selection: {e}")
            # Fallback to default agents
            return ["crop_selector", "farmer_coach"]
    
    def _format_agents_for_gemini(self) -> str:
        """Format agent information for Gemini prompt"""
        formatted_agents = []
        
        for agent_key, agent_info in self.available_agents.items():
            tools_str = ", ".join(agent_info.get("tools", [])) if agent_info.get("tools") else "None"
            formatted_agents.append(
                f"- {agent_key}: {agent_info['name']} - {agent_info['description']} (Tools: {tools_str})"
            )
        
        return "\n".join(formatted_agents)
    
    def _parse_agent_selection(self, response: str) -> List[str]:
        """Parse agent selection from Gemini response"""
        try:
            # Try to extract JSON from the response
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                # Try to find JSON array in the response
                start = response.find('[')
                end = response.rfind(']') + 1
                json_str = response[start:end]
            
            agent_list = json.loads(json_str)
            
            if isinstance(agent_list, list):
                return agent_list
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error parsing agent selection: {e}")
            return []
    
    async def _execute_agents(
        self, 
        agent_names: List[str], 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Execute the selected agents and collect their responses
        """
        agent_responses = []
        
        # Execute agents in parallel for better performance
        tasks = []
        for agent_name in agent_names:
            task = asyncio.create_task(self._execute_single_agent(agent_name, query, context))
            tasks.append(task)
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_responses.append(AgentResponse(
                    agent_name=agent_names[i],
                    success=False,
                    data={},
                    error=str(result)
                ))
            else:
                agent_responses.append(result)
        
        return agent_responses
    
    async def _execute_single_agent(
        self, 
        agent_name: str, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute a single agent with tools and context
        """
        start_time = datetime.now()
        
        try:
            self.logger.debug(f"Executing agent: {agent_name}")
            
            # Handle special General Chat agent
            if agent_name == "__general_chat__":
                response_text = await self._handle_general_conversation(query, context)
                execution_time = (datetime.now() - start_time).total_seconds()
                return AgentResponse(
                    agent_name="__general_chat__",
                    success=True,
                    data={"answer": response_text},
                    execution_time=execution_time
                )

            # Create agent instance from registry
            agent = self.agent_registry.create_agent(agent_name)
            
            # Prepare inputs with tools and context
            agent_tools = self._get_agent_tools(agent_name)
            inputs = {
                "query": query,
                "context": context or {},
                "tools": agent_tools,
                "session_id": context.get("session_id") if context else None
            }
            
            self.logger.debug(
                f"Agent {agent_name} inputs prepared",
                extra={
                    "tools_available": list(agent_tools.keys()),
                    "context_keys": list(context.keys()) if context else []
                }
            )
            
            # Execute the agent with timeout
            try:
                result = await asyncio.wait_for(agent.handle(inputs), timeout=30.0)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Agent {agent_name} execution timed out after 30 seconds")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Agent {agent_name} executed successfully",
                extra={
                    "execution_time": execution_time,
                    "result_keys": list(result.keys()) if isinstance(result, dict) else "non_dict_result"
                }
            )
            
            return AgentResponse(
                agent_name=agent_name,
                success=True,
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                f"Error executing agent {agent_name}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": execution_time
                },
                exc_info=True
            )
            
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
    
    def _get_agent_tools(self, agent_name: str) -> Dict[str, Any]:
        """Get tools available to a specific agent"""
        agent_info = self.available_agents.get(agent_name, {})
        agent_tools = agent_info.get("tools", [])
        
        available_tools = {}
        for tool_name in agent_tools:
            if tool_name in self.tools:
                available_tools[tool_name] = self.tools[tool_name]
        
        return available_tools
    
    def _format_agent_responses_for_synthesis(self, responses: List[AgentResponse]) -> str:
        """Format agent responses for synthesis"""
        formatted = []
        for r in responses:
            if not r.success:
                continue
                
            # Extract main response text
            response_text = ""
            if isinstance(r.data, dict):
                response_text = r.data.get("response", "")
                # If response is empty but data exists, try to format data
                if not response_text and r.data:
                    response_text = json.dumps(r.data, ensure_ascii=False)
            else:
                response_text = str(r.data)
                
            formatted.append(f"--- Agent: {r.agent_name} ---\n{response_text}\n")
            
        return "\n".join(formatted)

    async def _synthesize_response(
        self, 
        query: str, 
        agent_responses: List[AgentResponse], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize a comprehensive response from multiple agent responses
        """
        # Optimization: Pass through General Chat response directly
        if len(agent_responses) == 1 and agent_responses[0].agent_name == "__general_chat__" and agent_responses[0].success:
            return agent_responses[0].data

        # Optimization: If only one agent succeeded and we have structured data, skip synthesis LLM
        # to reduce latency.
        successful_agents = [r for r in agent_responses if r.success]
        if len(successful_agents) == 1 and not getattr(settings, "force_synthesis", False):
             return self._build_natural_response_from_agents(query, agent_responses)

        # Low-LLM mode: deterministic SOP assembly to reduce quota usage
        if getattr(settings, "low_llm_mode", False):
            return self._build_natural_response_from_agents(query, agent_responses)

        # Prepare agent responses for Gemini
        responses_text = self._format_agent_responses_for_synthesis(agent_responses)

        # Determine language for response
        locale = context.get('locale', 'en-IN') if context else 'en-IN'
        language_instruction = ""
        if locale and locale.lower() not in ('en', 'en-us', 'en-in', 'none'):
             language_instruction = f"\n\nIMPORTANT: Write the entire response in the language for locale '{locale}'."

        prompt = f"""
You are FarmXpert, a master agricultural consultant.
User Query: "{query}"

We have gathered insights from specialized agents:
{responses_text}

TASK:
Synthesize these inputs into a single, cohesive, and expert-level natural language response.

CRITICAL INSTRUCTIONS:
1.  **Pure Conversational Style**: Write like a human expert talking to a farmer. Do NOT use Markdown tables, data grids, or complex structured formats.
2.  **Preserve Details**: Use specific numbers, dates, prices, and names (e.g., "7.1 tons", "₹3500", "Start sowing on Nov 15") woven naturally into sentences or simple bullet points.
3.  **Unified Voice**: Do not say "The Yield Agent said...". Speak as one expert system.
4.  **No Fluff**: Get straight to the point.
5.  **Completeness**: If an agent provided a specific warning or risk, include it.

{language_instruction}

Response Format (JSON):
{{
"response": "The synthesized answer (pure markdown text, no tables)",
"recommendations": ["list", "of", "key", "actions"],
"warnings": ["critical", "warnings"],
"insights": ["key", "insights"]
}}
"""
        try:
            response = await gemini_service.generate_response(prompt, {"task": "synthesis"})
            
            # Parse JSON
            try:
                if '```json' in response:
                    start = response.find('```json') + 7
                    end = response.find('```', start)
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
                elif '{' in response:
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
                
            # Fallback
            return {
                "response": response,
                "recommendations": [],
                "warnings": [],
                "insights": []
            }
            
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return self._build_natural_response_from_agents(query, agent_responses)

    def _build_natural_response_from_agents(self, query: str, agent_responses: List[AgentResponse]) -> Dict[str, Any]:
        """Build natural language response from agent data when Gemini synthesis fails"""
        agents_used = [r.agent_name for r in agent_responses if r.success]
        
        # Build sentences from agent data
        sentences = []
        
        weather_data = None
        crop_data = None
        intro = ""
        
        # extract context first
        for r in agent_responses:
            if not r.success: continue
            if "weather" in r.agent_name.lower() and isinstance(r.data, dict):
                weather_data = r.data
            if ("crop" in r.agent_name.lower() or "growth" in r.agent_name.lower()) and isinstance(r.data, dict):
                crop_data = r.data
        
        # Create a contextual opening
        if weather_data and isinstance(weather_data, dict):
            temp = weather_data.get("temperature") or weather_data.get("current_temp")
            condition = weather_data.get("condition") or weather_data.get("weather")
            if temp and condition:
                intro = f"With the current {condition} conditions and {temp}°C temperature,"
        
        if intro:
            sentences.append(intro)
        
        for r in agent_responses:
            if not (r.success and isinstance(r.data, dict)):
                continue
            
            # Extract main content
            content = r.data.get("response") or r.data.get("answer") or r.data.get("message")
            if content:
                # specific clean up to ensure it flows
                text = str(content).strip()
                if not text.endswith('.'):
                    text += '.'
                sentences.append(text)
                
            # Extract specific recommendation if present
            recs = r.data.get("recommendations", [])
            if recs and isinstance(recs, list) and len(recs) > 0:
                rec_text = str(recs[0]).strip()
                # Clean up if it starts with "Recommended crop:" or similar redundant prefixes
                lower_rec = rec_text.lower()
                if "recommended crop:" in lower_rec:
                    rec_text = rec_text.split(":", 1)[1].strip()
                elif "recommendation:" in lower_rec:
                    rec_text = rec_text.split(":", 1)[1].strip()
                
                if rec_text:
                    sentences.append(f"I recommend {rec_text[0].lower() + rec_text[1:]}.")

        if len(sentences) <= 1:
            sentences.append("I don't have enough specific details to give you a complete answer. Please share your crop type and location so I can help you better.")
            
        full_text = " ".join(sentences)
        
        # Return structured as "answer" only, mimicking the LLM output
        return {
            "answer": full_text,
            "recommendations": [],
            "warnings": [],
            "next_steps": [],
            "meta": {
                "agents_used": agents_used,
                "confidence": 0.6 if agents_used else 0.4,
            },
        }
    
    def _format_agent_responses_for_synthesis(self, agent_responses: List[AgentResponse]) -> str:
        """Format agent responses for synthesis prompt"""
        formatted_responses = []
        
        for response in agent_responses:
            if response.success:
                agent_info = self.available_agents.get(response.agent_name, {})
                agent_name = agent_info.get("name", response.agent_name)
                
                formatted_responses.append(
                    f"**{agent_name}:**\n"
                    f"Response: {json.dumps(response.data, indent=2)}\n"
                    f"Execution Time: {response.execution_time:.2f}s\n"
                )
            else:
                formatted_responses.append(
                    f"**{response.agent_name}:**\n"
                    f"Error: {response.error}\n"
                )
        
        return "\n".join(formatted_responses)
    
    def _fallback_response_synthesis(self, agent_responses: List[AgentResponse]) -> str:
        """Fallback response synthesis when Gemini fails"""
        successful_responses = [r for r in agent_responses if r.success]
        
        if not successful_responses:
            return "I apologize, but I encountered issues while processing your query. Please try rephrasing your question or contact support for assistance."
        
        response_parts = []
        response_parts.append("Based on the analysis from our agricultural experts, here's what I found:\n")
        
        for response in successful_responses:
            agent_info = self.available_agents.get(response.agent_name, {})
            agent_name = agent_info.get("name", response.agent_name)
            
            response_parts.append(f"**{agent_name}:**")
            if isinstance(response.data, dict):
                for key, value in response.data.items():
                    response_parts.append(f"- {key}: {value}")
            else:
                response_parts.append(f"- {response.data}")
            response_parts.append("")
        
        return "\n".join(response_parts)


# Global instance
super_agent = SuperAgent()
