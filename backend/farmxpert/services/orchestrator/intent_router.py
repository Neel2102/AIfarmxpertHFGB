"""
Intent Router and Agent Response Scope Control Layer
Classifies user intents, routes queries to appropriate specialized agents,
and enforces strict response topic constraints.
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
    MARKET_PRICES = "MARKET_PRICES"
    IRRIGATION = "IRRIGATION"
    PEST_DISEASE = "PEST_DISEASE"
    YIELD_PREDICTION = "YIELD_PREDICTION"
    TASK_SCHEDULING = "TASK_SCHEDULING"
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
    selected_agent: str = "WeatherAgent"
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
                agent_name="WeatherAgent",
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
                agent_name="SoilHealthAgent",
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
            IntentType.MARKET_PRICES: AgentPolicy(
                agent_name="MarketIntelligenceAgent",
                primary_intent=IntentType.MARKET_PRICES,
                allowed_topics=[
                    "mandi prices", "commodity rates", "modal price", "min/max price",
                    "market arrivals", "price trends", "APMC"
                ],
                forbidden_topics=[
                    "soil testing", "weather forecast", "drip irrigation"
                ],
                available_tools=["get_market_prices"],
                response_style="commodity pricing per quintal, trends, and market locations"
            ),
            IntentType.IRRIGATION: AgentPolicy(
                agent_name="IrrigationAgent",
                primary_intent=IntentType.IRRIGATION,
                allowed_topics=[
                    "watering needs", "irrigation timing", "rainfall compensation",
                    "soil moisture deficit", "drip/sprinkler runtime"
                ],
                forbidden_topics=[
                    "mandi prices", "seed certified varieties"
                ],
                available_tools=["get_farm_weather", "get_sensor_data", "get_soil_data"],
                response_style="specific watering guidance based on soil moisture and upcoming rain"
            ),
            IntentType.CROP_SELECTION: AgentPolicy(
                agent_name="CropSelectorAgent",
                primary_intent=IntentType.CROP_SELECTION,
                allowed_topics=[
                    "crop recommendations", "season suitability", "soil compatibility",
                    "seed varieties", "crop duration"
                ],
                forbidden_topics=[
                    "weather forecasts", "detailed mandi price tables"
                ],
                available_tools=["get_crop_recommendations", "get_soil_data"],
                response_style="curated crop choices suited to farm soil and season"
            ),
            IntentType.PEST_DISEASE: AgentPolicy(
                agent_name="PestDiseaseAgent",
                primary_intent=IntentType.PEST_DISEASE,
                allowed_topics=[
                    "symptoms", "pest identification", "disease diagnosis",
                    "treatment methods", "preventive sprays"
                ],
                forbidden_topics=[
                    "mandi prices", "soil testing"
                ],
                available_tools=["get_crop_recommendations", "get_farm_weather"],
                response_style="targeted treatment and chemical/organic controls"
            ),
            IntentType.YIELD_PREDICTION: AgentPolicy(
                agent_name="YieldPredictionAgent",
                primary_intent=IntentType.YIELD_PREDICTION,
                allowed_topics=["expected yield", "tonnage per acre", "yield factors", "harvest timing"],
                forbidden_topics=["weather forecasts", "mandi prices"],
                available_tools=["get_farm_status", "get_soil_data"],
                response_style="data-driven yield estimate"
            ),
            IntentType.TASK_SCHEDULING: AgentPolicy(
                agent_name="TaskSchedulerAgent",
                primary_intent=IntentType.TASK_SCHEDULING,
                allowed_topics=["farm schedule", "daily tasks", "pending work", "field operations"],
                forbidden_topics=["unrelated generic farming recommendations"],
                available_tools=["get_farm_tasks"],
                response_style="organized operational checklist"
            ),
            IntentType.FARM_STATUS: AgentPolicy(
                agent_name="FarmMonitoringAgent",
                primary_intent=IntentType.FARM_STATUS,
                allowed_topics=["farm summary", "active crops", "current fields", "system health"],
                forbidden_topics=["generic advice"],
                available_tools=["get_farm_status", "get_sensor_data", "get_farm_tasks"],
                response_style="executive farm operational overview"
            ),
            IntentType.SENSOR_DATA: AgentPolicy(
                agent_name="SensorAgent",
                primary_intent=IntentType.SENSOR_DATA,
                allowed_topics=["sensor values", "moisture level", "temperature", "EC", "Blynk status"],
                forbidden_topics=["generic advice"],
                available_tools=["get_sensor_data"],
                response_style="direct telemetry readings"
            ),
            IntentType.GENERAL_FARMING: AgentPolicy(
                agent_name="FarmerCoachAgent",
                primary_intent=IntentType.GENERAL_FARMING,
                allowed_topics=["agricultural guidance", "farming concepts"],
                forbidden_topics=[],
                available_tools=[],
                response_style="helpful, consultative"
            ),
            IntentType.UNKNOWN: AgentPolicy(
                agent_name="Orchestrator",
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
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> RoutedIntent:
        """
        Classify intent and determine required tools and agent policy.
        Preserves multi-turn context (e.g. 'What about tomorrow?').
        """
        q = (query or "").lower().strip()

        # Check for ambiguous queries (STEP 3)
        ambiguous_queries = {"give me advice", "give advice", "advice", "help me", "help", "what should i do", "guide me"}
        if q in ambiguous_queries:
            return RoutedIntent(
                primary_intent=IntentType.UNKNOWN,
                is_ambiguous=True,
                clarification_message=(
                    "I'm here to help with your farm! Could you specify what you need guidance on?\n\n"
                    "1. 🌦️ **Weather & Forecasts** (e.g., 'What's the weather today?')\n"
                    "2. 💧 **Irrigation Guidance** (e.g., 'Should I irrigate my field tomorrow?')\n"
                    "3. 🧪 **Soil Health & Nutrients** (e.g., 'How healthy is my soil?')\n"
                    "4. 📈 **Mandi Market Prices** (e.g., 'What is the price of cotton?')\n"
                    "5. 🌱 **Crop Selection & Planning** (e.g., 'Which crop should I plant?')"
                )
            )

        # Multi-turn follow-up detection (STEP 12)
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

        def contains_word(words: List[str]) -> bool:
            return any(re.search(r"\b" + re.escape(w) + r"\b", q) for w in words)

        # 1. Weather keywords
        wants_weather = contains_word([
            "weather", "rain", "rainfall", "forecast", "temperature", "temp",
            "humidity", "wind", "storm", "drizzle", "monsoon", "cloudy", "sunny", "heatwave"
        ])

        # 2. Irrigation keywords
        wants_irrigation = contains_word([
            "irrigation", "irrigate", "watering", "water my", "drip", "sprinkler", "borewell"
        ])

        # 3. Market keywords
        wants_market = contains_word([
            "mandi", "price", "prices", "apmc", "market price", "selling price",
            "bhav", "rate", "cost of cotton", "price of wheat"
        ])

        # 4. Soil health keywords
        wants_soil = contains_word([
            "soil", "soil health", "npk", "nitrogen", "phosphorus", "potassium",
            "ph level", "organic carbon", "fertilizer dose", "soil test"
        ])

        # 5. Crop selection keywords
        wants_crop_selection = contains_word([
            "which crop", "what crop", "what should i plant", "crop selection",
            "what to sow", "which variety", "seed recommendation", "grow this season", "plant this season"
        ])

        # 6. Pest & Disease keywords
        wants_pest = contains_word([
            "pest", "disease", "fungus", "infection", "spots on leaves",
            "yellow leaves", "caterpillar", "blight", "borer", "spray for"
        ])

        # 7. Yield prediction keywords
        wants_yield = contains_word([
            "yield", "how much production", "expected harvest", "tons per acre", "quintals per acre"
        ])

        # 8. Task scheduling keywords
        wants_tasks = contains_word([
            "tasks", "task list", "scheduled tasks", "what work today", "schedule today", "pending work"
        ])

        # 9. Sensor keywords
        wants_sensor = contains_word([
            "sensor", "sensors", "blynk", "iot reading", "telemetry"
        ])

        # 10. Farm status
        wants_status = contains_word([
            "farm status", "farm summary", "overview of my farm", "my farm details"
        ])

        # Composite routing (STEP 3 Examples):
        # "Should I irrigate my cotton field today?" -> IRRIGATION + WEATHER
        if wants_irrigation:
            policy = self._policies[IntentType.IRRIGATION]
            sec = [IntentType.WEATHER] if wants_weather or "today" in q or "tomorrow" in q else []
            return RoutedIntent(
                primary_intent=IntentType.IRRIGATION,
                secondary_intents=sec,
                selected_agent=policy.agent_name,
                tools_needed=list(set(policy.available_tools + ["get_farm_weather"])),
                policy=policy
            )

        # "Will the rain affect my cotton crop?" -> WEATHER + agricultural reasoning
        if wants_weather and ("affect" in q or "impact" in q or "cotton" in q or "crop" in q or "wheat" in q):
            policy = self._policies[IntentType.WEATHER]
            return RoutedIntent(
                primary_intent=IntentType.WEATHER,
                secondary_intents=[IntentType.CROP_SELECTION],
                selected_agent=policy.agent_name,
                tools_needed=["get_farm_weather"],
                policy=policy
            )

        # Pure Weather: "Give me weather updates for my farm"
        if wants_weather:
            policy = self._policies[IntentType.WEATHER]
            return RoutedIntent(
                primary_intent=IntentType.WEATHER,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Market prices: "What is the mandi price of cotton?"
        if wants_market:
            policy = self._policies[IntentType.MARKET_PRICES]
            return RoutedIntent(
                primary_intent=IntentType.MARKET_PRICES,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Soil health: "How healthy is my soil?"
        if wants_soil:
            policy = self._policies[IntentType.SOIL_HEALTH]
            return RoutedIntent(
                primary_intent=IntentType.SOIL_HEALTH,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Crop selection: "Which crop should I plant this season?"
        if wants_crop_selection:
            policy = self._policies[IntentType.CROP_SELECTION]
            return RoutedIntent(
                primary_intent=IntentType.CROP_SELECTION,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Pest & Disease
        if wants_pest:
            policy = self._policies[IntentType.PEST_DISEASE]
            return RoutedIntent(
                primary_intent=IntentType.PEST_DISEASE,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Yield
        if wants_yield:
            policy = self._policies[IntentType.YIELD_PREDICTION]
            return RoutedIntent(
                primary_intent=IntentType.YIELD_PREDICTION,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Tasks
        if wants_tasks:
            policy = self._policies[IntentType.TASK_SCHEDULING]
            return RoutedIntent(
                primary_intent=IntentType.TASK_SCHEDULING,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Sensor
        if wants_sensor:
            policy = self._policies[IntentType.SENSOR_DATA]
            return RoutedIntent(
                primary_intent=IntentType.SENSOR_DATA,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # Status
        if wants_status:
            policy = self._policies[IntentType.FARM_STATUS]
            return RoutedIntent(
                primary_intent=IntentType.FARM_STATUS,
                selected_agent=policy.agent_name,
                tools_needed=policy.available_tools,
                policy=policy
            )

        # General farming question
        policy = self._policies[IntentType.GENERAL_FARMING]
        return RoutedIntent(
            primary_intent=IntentType.GENERAL_FARMING,
            selected_agent=policy.agent_name,
            tools_needed=[],
            policy=policy
        )


# Global intent router instance
intent_router = IntentRouter()
