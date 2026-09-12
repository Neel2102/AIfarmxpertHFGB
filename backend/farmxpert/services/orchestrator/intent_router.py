"""
Intent Router and Agent Response Scope Control Layer
Classifies user intents, routes queries to appropriate specialized agents registered in AgentRegistry,
and enforces response topic constraints.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from farmxpert.core.utils.logger import get_logger

logger = get_logger("intent_router")


class IntentType(str, Enum):
    WEATHER = "WEATHER"
    SOIL_HEALTH = "SOIL_HEALTH"
    CROP_SELECTION = "CROP_SELECTION"
    FERTILIZER = "FERTILIZER"
    MARKET_PRICES = "MARKET_PRICES"
    IRRIGATION = "IRRIGATION"
    PEST_DISEASE = "PEST_DISEASE"
    YIELD_PREDICTION = "YIELD_PREDICTION"
    TASK_SCHEDULING = "TASK_SCHEDULING"
    GROWTH_STAGE = "GROWTH_STAGE"
    FARM_STATUS = "FARM_STATUS"
    SENSOR_DATA = "SENSOR_DATA"
    GENERAL_FARMING = "GENERAL_FARMING"
    UNKNOWN = "UNKNOWN"


@dataclass
class AgentPolicy:
    agent_name: str
    primary_intent: IntentType
    allowed_topics: List[str]
    forbidden_topics: List[str]
    available_tools: List[str]
    response_style: str = "concise, direct, data-focused"


@dataclass
class RoutedIntent:
    primary_intent: IntentType
    secondary_intents: List[IntentType] = field(default_factory=list)
    selected_agent: str = "weather_watcher"
    tools_needed: List[str] = field(default_factory=list)
    is_ambiguous: bool = False
    clarification_message: Optional[str] = None
    policy: Optional[AgentPolicy] = None


class IntentRouter:
    """Deterministic, pattern-aware and conversational intent router."""

    def __init__(self):
        self._policies: Dict[IntentType, AgentPolicy] = self._build_policies()

    def _build_policies(self) -> Dict[IntentType, AgentPolicy]:
        return {
            IntentType.WEATHER: AgentPolicy(
                agent_name="weather_watcher",
                primary_intent=IntentType.WEATHER,
                allowed_topics=[
                    "current weather", "forecast", "rainfall", "temperature",
                    "humidity", "wind speed", "precipitation chance", "weather alerts"
                ],
                forbidden_topics=[
                    "soil testing", "NPK", "synthetic nitrogen", "certified seeds",
                    "mandi prices", "APMC", "drip irrigation setup", "grain terminals"
                ],
                available_tools=["get_farm_weather"],
                response_style="pure weather focus, clear figures and alerts"
            ),
            IntentType.SOIL_HEALTH: AgentPolicy(
                agent_name="soil_health",
                primary_intent=IntentType.SOIL_HEALTH,
                allowed_topics=[
                    "soil pH", "NPK levels", "nitrogen", "phosphorus", "potassium",
                    "soil moisture", "organic carbon", "electrical conductivity", "soil amendments"
                ],
                forbidden_topics=[
                    "weather forecasts", "mandi prices", "APMC market rates"
                ],
                available_tools=["get_soil_data", "get_sensor_data"],
                response_style="nutrient metrics and soil conditioning"
            ),
            IntentType.CROP_SELECTION: AgentPolicy(
                agent_name="crop_selector",
                primary_intent=IntentType.CROP_SELECTION,
                allowed_topics=[
                    "crop recommendations", "season suitability", "soil compatibility",
                    "seed varieties", "crop duration"
                ],
                forbidden_topics=[
                    "detailed mandi price tables", "equipment maintenance"
                ],
                available_tools=["get_crop_recommendations", "get_soil_data", "get_farm_weather"],
                response_style="curated crop choices suited to farm soil and season"
            ),
            IntentType.FERTILIZER: AgentPolicy(
                agent_name="fertilizer_advisor",
                primary_intent=IntentType.FERTILIZER,
                allowed_topics=[
                    "fertilizer recommendations", "NPK ratio", "urea", "DAP", "organic manure",
                    "application timing", "fertilizer dosage"
                ],
                forbidden_topics=[
                    "mandi prices", "machinery purchase"
                ],
                available_tools=["get_soil_data", "get_sensor_data"],
                response_style="precise fertilizer application dosage and schedule"
            ),
            IntentType.MARKET_PRICES: AgentPolicy(
                agent_name="market_intelligence",
                primary_intent=IntentType.MARKET_PRICES,
                allowed_topics=[
                    "mandi prices", "commodity rates", "modal price", "min/max price",
                    "market arrivals", "price trends", "APMC", "market situation"
                ],
                forbidden_topics=[
                    "soil testing", "weather forecast", "drip irrigation"
                ],
                available_tools=["get_market_prices"],
                response_style="commodity pricing per quintal, trends, and market locations"
            ),
            IntentType.IRRIGATION: AgentPolicy(
                agent_name="irrigation_planner",
                primary_intent=IntentType.IRRIGATION,
                allowed_topics=[
                    "watering needs", "irrigation timing", "rainfall compensation",
                    "soil moisture deficit", "drip/sprinkler runtime", "low soil moisture"
                ],
                forbidden_topics=[
                    "mandi prices", "seed certified varieties"
                ],
                available_tools=["get_farm_weather", "get_sensor_data", "get_soil_data"],
                response_style="specific watering guidance based on soil moisture and upcoming rain"
            ),
            IntentType.PEST_DISEASE: AgentPolicy(
                agent_name="pest_disease_diagnostic",
                primary_intent=IntentType.PEST_DISEASE,
                allowed_topics=[
                    "symptoms", "pest identification", "disease diagnosis",
                    "treatment methods", "preventive sprays", "fungus", "insects"
                ],
                forbidden_topics=[
                    "mandi prices", "soil testing"
                ],
                available_tools=["get_crop_recommendations", "get_farm_weather"],
                response_style="targeted treatment and chemical/organic controls"
            ),
            IntentType.YIELD_PREDICTION: AgentPolicy(
                agent_name="yield_predictor",
                primary_intent=IntentType.YIELD_PREDICTION,
                allowed_topics=["expected yield", "tonnage per acre", "yield factors", "harvest timing", "production forecast"],
                forbidden_topics=["weather forecasts", "mandi prices"],
                available_tools=["get_farm_status", "get_soil_data", "get_farm_weather"],
                response_style="data-driven yield estimate"
            ),
            IntentType.TASK_SCHEDULING: AgentPolicy(
                agent_name="task_scheduler",
                primary_intent=IntentType.TASK_SCHEDULING,
                allowed_topics=["farm schedule", "daily tasks", "pending work", "field operations", "today's tasks"],
                forbidden_topics=["unrelated generic farming recommendations"],
                available_tools=["get_farm_tasks"],
                response_style="organized operational checklist"
            ),
            IntentType.GROWTH_STAGE: AgentPolicy(
                agent_name="growth_stage_monitor",
                primary_intent=IntentType.GROWTH_STAGE,
                allowed_topics=["crop stage", "vegetative", "flowering", "maturity", "harvest date"],
                forbidden_topics=["mandi prices"],
                available_tools=["get_farm_status", "get_crop_recommendations"],
                response_style="stage tracking and upcoming milestones"
            ),
            IntentType.FARM_STATUS: AgentPolicy(
                agent_name="weather_watcher",
                primary_intent=IntentType.FARM_STATUS,
                allowed_topics=["farm summary", "active crops", "current fields", "system health", "farm conditions"],
                forbidden_topics=["generic advice"],
                available_tools=["get_farm_status", "get_sensor_data", "get_farm_weather", "get_farm_tasks"],
                response_style="executive farm operational overview"
            ),
            IntentType.SENSOR_DATA: AgentPolicy(
                agent_name="soil_health",
                primary_intent=IntentType.SENSOR_DATA,
                allowed_topics=["sensor values", "moisture level", "temperature", "EC", "Blynk status"],
                forbidden_topics=["generic advice"],
                available_tools=["get_sensor_data", "get_soil_data"],
                response_style="direct telemetry readings"
            ),
            IntentType.GENERAL_FARMING: AgentPolicy(
                agent_name="farmer_coach",
                primary_intent=IntentType.GENERAL_FARMING,
                allowed_topics=["agricultural guidance", "farming concepts"],
                forbidden_topics=[],
                available_tools=[],
                response_style="helpful, consultative"
            ),
            IntentType.UNKNOWN: AgentPolicy(
                agent_name="farmer_coach",
                primary_intent=IntentType.UNKNOWN,
                allowed_topics=[],
                forbidden_topics=[],
                available_tools=[],
                response_style="clarification request"
            ),
        }

    def route_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        forced_agent: Optional[str] = None
    ) -> RoutedIntent:
        """
        Classify intent and determine required tools and agent policy.
        Preserves multi-turn context and handles natural farmer queries accurately.
        """
        q = (query or "").lower().strip()

        # If frontend explicitly targeted an agent (e.g. user chatting on a specialized agent tab)
        if forced_agent and forced_agent != "super-agent":
            # Map frontend names to policies
            agent_intent_map = {
                "soil_health": IntentType.SOIL_HEALTH,
                "soil_health_agent": IntentType.SOIL_HEALTH,
                "task_scheduler": IntentType.TASK_SCHEDULING,
                "task_scheduler_agent": IntentType.TASK_SCHEDULING,
                "crop_selector": IntentType.CROP_SELECTION,
                "market_intelligence": IntentType.MARKET_PRICES,
                "market_intelligence_agent": IntentType.MARKET_PRICES,
                "yield_predictor": IntentType.YIELD_PREDICTION,
                "fertilizer_advisor": IntentType.FERTILIZER,
                "fertilizer_agent": IntentType.FERTILIZER,
                "irrigation_planner": IntentType.IRRIGATION,
                "irrigation_agent": IntentType.IRRIGATION,
                "weather_watcher": IntentType.WEATHER,
                "pest_disease_diagnostic": IntentType.PEST_DISEASE,
                "growth_stage_monitor": IntentType.GROWTH_STAGE,
                "farmer_coach": IntentType.GENERAL_FARMING,
            }
            mapped_intent = agent_intent_map.get(forced_agent)
            if mapped_intent and mapped_intent in self._policies:
                policy = self._policies[mapped_intent]
                return RoutedIntent(
                    primary_intent=mapped_intent,
                    selected_agent=policy.agent_name,
                    tools_needed=policy.available_tools,
                    policy=policy
                )

        # Ambiguous general greeting checks
        ambiguous_queries = {"give me advice", "give advice", "advice", "help me", "help", "what should i do", "guide me"}
        if q in ambiguous_queries:
            return RoutedIntent(
                primary_intent=IntentType.UNKNOWN,
                selected_agent="farmer_coach",
                is_ambiguous=True,
                clarification_message=(
                    "I'm here to help with your farm operations! What would you like assistance with?\n\n"
                    "1. 🌦️ **Weather & Forecasts** (e.g., 'Will it rain today?')\n"
                    "2. 💧 **Irrigation Guidance** (e.g., 'Should I irrigate today? What about low soil moisture?')\n"
                    "3. 🧪 **Soil Health & Fertilizer** (e.g., 'What is my soil health? What fertilizer to use?')\n"
                    "4. 🌱 **Crop Planning & Selection** (e.g., 'Which crop should I plant this season?')\n"
                    "5. 📈 **Market Prices & Mandi** (e.g., 'What is the current market situation for cotton?')\n"
                    "6. 📋 **Daily Tasks** (e.g., 'Give me today's farming tasks')\n"
                    "7. 📊 **Yield Prediction** (e.g., 'Predict my yield for this season')"
                )
            )

        # Multi-turn follow-up detection
        if chat_history and len(chat_history) >= 2:
            last_assistant_msg = next((m["content"] for m in reversed(chat_history) if m.get("role") == "assistant"), "").lower()
            last_user_msg = next((m["content"] for m in reversed(chat_history) if m.get("role") == "user"), "").lower()

            is_followup_time = any(w in q for w in ["tomorrow", "day after", "next week", "this week", "yesterday", "weekend", "today", "what about tomorrow", "and tomorrow"])
            if is_followup_time and ("weather" in last_user_msg or "temperature" in last_user_msg or "rain" in last_user_msg or "°c" in last_assistant_msg or "humidity" in last_assistant_msg):
                policy = self._policies[IntentType.WEATHER]
                return RoutedIntent(
                    primary_intent=IntentType.WEATHER,
                    selected_agent=policy.agent_name,
                    tools_needed=policy.available_tools,
                    policy=policy
                )

        def contains_any(words: List[str]) -> bool:
            return any(w in q for w in words)

        def contains_word_regex(words: List[str]) -> bool:
            return any(re.search(r"\b" + re.escape(w) + r"\b", q) for w in words)

        # 1. TASK SCHEDULING (high priority match)
        # e.g. "Give me today's farming tasks.", "What tasks do I need to complete today?"
        if contains_any([
            "farming task", "today's task", "todays task", "task list", "pending task",
            "daily task", "tasks do i need", "tasks for today", "schedule today", "what work today", "schedule for today"
        ]) or (contains_word_regex(["task", "tasks", "schedule", "worklist", "checklist"]) and contains_any(["today", "farm", "complete", "pending", "do", "give me"])):
            policy = self._policies[IntentType.TASK_SCHEDULING]
            return RoutedIntent(
                primary_intent=IntentType.TASK_SCHEDULING,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 2. CROP SELECTION / RECOMMENDATION
        # e.g. "Which crop should I plant this season?", "What crops are suitable for my soil?"
        if contains_any([
            "which crop", "what crop", "which crops", "what crops", "suitable crop", "suitable crops",
            "crops are suitable", "crops suitable", "crop to plant", "crop to sow", "should i plant",
            "should i grow", "crop selection", "crop recommendation", "recommend a crop", "what to sow"
        ]) or (contains_word_regex(["crop", "crops", "plant", "sow"]) and contains_any(["season", "suitable", "soil", "grow", "recommend", "select", "which", "what"])):
            policy = self._policies[IntentType.CROP_SELECTION]
            return RoutedIntent(
                primary_intent=IntentType.CROP_SELECTION,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 3. YIELD PREDICTION
        # e.g. "Predict my yield.", "What will be my yield?"
        if contains_any([
            "predict my yield", "predict yield", "my yield", "expected yield", "crop yield",
            "how much yield", "production forecast", "expected harvest", "tons per acre", "quintals per acre"
        ]) or contains_word_regex(["yield", "production", "tonnage"]):
            policy = self._policies[IntentType.YIELD_PREDICTION]
            return RoutedIntent(
                primary_intent=IntentType.YIELD_PREDICTION,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 4. FERTILIZER ADVISOR
        # e.g. "What fertilizer should I use?", "What is the fertilizer dose?"
        if contains_any([
            "fertilizer", "fertiliser", "urea", "dap", "potash", "manure", "npk dose",
            "nutrient dose", "apply fertilizer", "which fertilizer", "what fertilizer", "compost"
        ]) or contains_word_regex(["fertilizer", "fertilizers", "fertiliser", "nutrients", "urea", "dap"]):
            policy = self._policies[IntentType.FERTILIZER]
            return RoutedIntent(
                primary_intent=IntentType.FERTILIZER,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 5. IRRIGATION & MOISTURE GUIDANCE
        # e.g. "Should I irrigate today?", "What should I do about low soil moisture?"
        if contains_any([
            "soil moisture", "low moisture", "low soil moisture", "irrigate", "irrigation",
            "should i water", "water my", "watering", "drip irrigation", "sprinkler", "borewell"
        ]) or contains_word_regex(["irrigate", "irrigation", "watering"]):
            policy = self._policies[IntentType.IRRIGATION]
            return RoutedIntent(
                primary_intent=IntentType.IRRIGATION,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 6. SOIL HEALTH & LAB TESTS
        # e.g. "What is the soil health of my farm?", "How healthy is my soil?"
        if contains_any([
            "soil health", "soil test", "soil condition", "soil quality", "ph level",
            "soil ph", "npk", "nitrogen", "phosphorus", "potassium", "organic carbon", "soil fertility"
        ]) or (contains_word_regex(["soil"]) and contains_any(["health", "status", "test", "condition", "quality", "nutrient", "ph", "carbon"])):
            policy = self._policies[IntentType.SOIL_HEALTH]
            return RoutedIntent(
                primary_intent=IntentType.SOIL_HEALTH,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 7. MARKET INTELLIGENCE & PRICES
        # e.g. "What is the current market situation?", "What is the price of cotton?"
        if contains_any([
            "market situation", "market price", "market prices", "mandi price", "mandi prices",
            "current market", "apmc", "mandi bhav", "rate of", "price of", "selling price", "commodity price"
        ]) or contains_word_regex(["mandi", "apmc", "bhav"]) or (contains_word_regex(["market", "price", "prices"]) and contains_any(["cotton", "wheat", "rice", "corn", "current", "situation", "rate", "today"])):
            policy = self._policies[IntentType.MARKET_PRICES]
            return RoutedIntent(
                primary_intent=IntentType.MARKET_PRICES,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 8. PEST & DISEASE DIAGNOSTIC
        # e.g. "My plants have yellow spots and pests"
        if contains_any([
            "pest", "disease", "fungus", "insects", "yellow leaves", "spots on leaves",
            "leaf blight", "caterpillar", "borer", "infestation", "spray for", "wilting"
        ]) or contains_word_regex(["pest", "pests", "disease", "diseases", "fungus", "insect", "insects"]):
            policy = self._policies[IntentType.PEST_DISEASE]
            return RoutedIntent(
                primary_intent=IntentType.PEST_DISEASE,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 9. FARM STATUS / CONDITIONS OVERVIEW
        # e.g. "Show me my farm's current conditions.", "What is the farm status?"
        if contains_any([
            "farm condition", "farm conditions", "current conditions", "farm status",
            "farm overview", "farm summary", "how is my farm"
        ]):
            policy = self._policies[IntentType.FARM_STATUS]
            return RoutedIntent(
                primary_intent=IntentType.FARM_STATUS,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 10. WEATHER & FORECAST
        # e.g. "Will it rain today?", "What is the weather?"
        if contains_any([
            "weather", "rain", "rainfall", "forecast", "temperature", "humidity",
            "precipitation", "wind speed", "heatwave", "storm", "cloudy", "sunny"
        ]) or contains_word_regex(["weather", "rain", "temp", "temperature", "forecast", "monsoon"]):
            policy = self._policies[IntentType.WEATHER]
            return RoutedIntent(
                primary_intent=IntentType.WEATHER,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 11. CROP GROWTH STAGE
        if contains_any(["growth stage", "crop stage", "growth monitor", "flowering stage", "vegetative stage"]):
            policy = self._policies[IntentType.GROWTH_STAGE]
            return RoutedIntent(
                primary_intent=IntentType.GROWTH_STAGE,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # 12. GENERAL FARMING / FARMER COACH FALLBACK
        policy = self._policies[IntentType.GENERAL_FARMING]
        return RoutedIntent(
            primary_intent=IntentType.GENERAL_FARMING,
            selected_agent=policy.agent_name,
            tools_needed=[],
            policy=policy
        )


# Global intent router instance
intent_router = IntentRouter()
