"""
Comprehensive Automated Test Suite for FarmXpert Multi-Agent Orchestrator
Tests:
- Intent routing for all core operational requests
- Tool execution scoping (only appropriate tools run)
- Exclusion of unrelated agents & generic farming advice
- Multi-farm selection & disambiguation
- Scoped authorization (rejecting unauthorized farm_id)
- Missing farm and missing coordinate handling
- Weather API failure handling
- Ambiguous query clarification
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from farmxpert.services.orchestrator.intent_router import intent_router, IntentType
from farmxpert.services.orchestrator.farm_context import (
    FarmContext, FarmContextResolver, FarmResolutionStatus
)
from farmxpert.services.orchestrator.tool_registry import tool_registry
from farmxpert.services.orchestrator.farmxpert_orchestrator import farmxpert_orchestrator
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, SoilTest, Crop


# ---------------------------------------------------------------------------
# FIXTURES & MOCK DATA
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user():
    user = User(
        id=101,
        username="farmer_rajesh",
        email="rajesh@farmxpert.test",
        full_name="Rajesh Patel",
        is_active=True
    )
    return user


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def farm_context_anand():
    return FarmContext(
        user_id=101,
        farm_id=1,
        farm_name="Anand Farm",
        latitude=22.56,
        longitude=72.95,
        location_name="Anand, Gujarat",
        district="Anand",
        state="Gujarat",
        crops=["Cotton", "Wheat"],
        soil_type="Sandy Loam",
        soil_data={"ph": 6.8, "moisture": 24.5, "nitrogen": 180, "phosphorus": 45, "potassium": 210}
    )


# ---------------------------------------------------------------------------
# TEST GROUP 1: INTENT ROUTING
# ---------------------------------------------------------------------------

def test_intent_weather_queries():
    """Verify that weather queries route strictly to WEATHER intent."""
    routed1 = intent_router.route_query("Give me weather updates for my farm")
    assert routed1.primary_intent == IntentType.WEATHER
    assert routed1.selected_agent == "WeatherAgent"
    assert "get_farm_weather" in routed1.tools_needed
    assert "get_market_prices" not in routed1.tools_needed
    assert "get_soil_data" not in routed1.tools_needed

    routed2 = intent_router.route_query("What's the weather tomorrow?")
    assert routed2.primary_intent == IntentType.WEATHER

    routed3 = intent_router.route_query("Is it going to rain this afternoon?")
    assert routed3.primary_intent == IntentType.WEATHER


def test_intent_weather_crop_reasoning():
    """Verify 'Will rain affect my cotton?' routes to WEATHER with crop reasoning."""
    routed = intent_router.route_query("Will rain affect my cotton?")
    assert routed.primary_intent == IntentType.WEATHER
    assert "get_farm_weather" in routed.tools_needed
    assert IntentType.CROP_SELECTION in routed.secondary_intents


def test_intent_market_prices():
    """Verify market queries route to MARKET_PRICES and do not call weather."""
    routed = intent_router.route_query("What's today's cotton mandi price?")
    assert routed.primary_intent == IntentType.MARKET_PRICES
    assert routed.selected_agent == "MarketIntelligenceAgent"
    assert "get_market_prices" in routed.tools_needed
    assert "get_farm_weather" not in routed.tools_needed


def test_intent_soil_health():
    """Verify soil health queries route to SOIL_HEALTH."""
    routed = intent_router.route_query("How healthy is my soil?")
    assert routed.primary_intent == IntentType.SOIL_HEALTH
    assert routed.selected_agent == "SoilHealthAgent"
    assert "get_soil_data" in routed.tools_needed
    assert "get_farm_weather" not in routed.tools_needed


def test_intent_irrigation_plus_weather():
    """Verify irrigation queries combine IRRIGATION and WEATHER data."""
    routed = intent_router.route_query("Should I irrigate my cotton field tomorrow?")
    assert routed.primary_intent == IntentType.IRRIGATION
    assert "get_farm_weather" in routed.tools_needed


def test_intent_crop_selection():
    """Verify crop selection queries route to CROP_SELECTION."""
    routed = intent_router.route_query("Which crop should I plant this season?")
    assert routed.primary_intent == IntentType.CROP_SELECTION
    assert "get_crop_recommendations" in routed.tools_needed
    assert "get_market_prices" not in routed.tools_needed


def test_ambiguous_query_asks_clarification():
    """Verify 'Give me advice' asks for clarification rather than triggering all agents."""
    routed = intent_router.route_query("Give me advice")
    assert routed.is_ambiguous is True
    assert routed.clarification_message is not None
    assert len(routed.tools_needed) == 0


def test_multi_turn_followup_preserves_weather_intent():
    """Verify multi-turn 'What about tomorrow?' preserves WEATHER intent."""
    history = [
        {"role": "user", "content": "How is the weather today?"},
        {"role": "assistant", "content": "Today's weather at your farm: 29°C and cloudy."}
    ]
    routed = intent_router.route_query("What about tomorrow?", chat_history=history)
    assert routed.primary_intent == IntentType.WEATHER
    assert "get_farm_weather" in routed.tools_needed


# ---------------------------------------------------------------------------
# TEST GROUP 2: TOOL PERMISSIONS & ZERO FABRICATION
# ---------------------------------------------------------------------------

def test_tool_permissions_strict():
    """Verify that WEATHER intent only grants access to weather tools."""
    tools = tool_registry.get_tools_for_intent("WEATHER")
    tool_names = [t.name for t in tools]
    assert "get_farm_weather" in tool_names
    assert "get_soil_data" not in tool_names
    assert "get_market_prices" not in tool_names
    assert "get_farm_tasks" not in tool_names


@pytest.mark.asyncio
async def test_weather_tool_missing_coordinates(mock_db):
    """Verify that weather tool reports missing coordinates without fabricating."""
    empty_context = FarmContext(user_id=101, farm_id=1, latitude=None, longitude=None)
    result = await tool_registry.execute_tool("get_farm_weather", farm_context=empty_context, db=mock_db)
    assert result.success is False
    assert "coordinates" in result.error.lower() or "location" in result.error.lower()


@pytest.mark.asyncio
async def test_weather_tool_live_or_graceful_unavailable(farm_context_anand, mock_db):
    """Verify real weather tool execution returns structured data or graceful unavailability."""
    result = await tool_registry.execute_tool(
        "get_farm_weather",
        farm_context=farm_context_anand,
        db=mock_db,
        arguments={"forecast_days": 2}
    )
    if result.success:
        assert "current" in result.data
        assert "temperature_c" in result.data["current"]
        assert "humidity_percent" in result.data["current"]
        assert "rain_probability_percent" in result.data["current"]
    else:
        assert "unavailable" in result.error.lower()


# ---------------------------------------------------------------------------
# TEST GROUP 3: CONTEXT RESOLUTION & SECURITY (STEP 5 & 13)
# ---------------------------------------------------------------------------

def test_unauthorized_farm_access_rejected(test_user, mock_db):
    """Verify that requesting another user's farm is rejected with UNAUTHORIZED."""
    # Mock user having farm #1, but requesting farm #999
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="My Farm", latitude=22.0, longitude=73.0)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    res = FarmContextResolver.resolve(db=mock_db, user=test_user, requested_farm_id=999)
    assert res.status == FarmResolutionStatus.UNAUTHORIZED
    assert "access denied" in res.message.lower()


def test_multi_farm_selection_prompt(test_user, mock_db):
    """Verify that a user with multiple farms is asked to select one."""
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="Vadodara Farm", district="Vadodara", state="Gujarat", latitude=22.3, longitude=73.2)
    farm2 = Farm(id=2, user_id=test_user.id, farm_name="Anand Farm", district="Anand", state="Gujarat", latitude=22.5, longitude=72.9)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1, farm2]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    res = FarmContextResolver.resolve(db=mock_db, user=test_user, requested_farm_id=None, query="Give me weather updates for my farm")
    assert res.status == FarmResolutionStatus.NEEDS_SELECTION
    assert len(res.available_farms) == 2
    assert "Vadodara Farm" in res.message
    assert "Anand Farm" in res.message


def test_multi_farm_resolved_by_query_mention(test_user, mock_db):
    """Verify that mentioning farm location in query automatically selects it."""
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="Vadodara Farm", district="Vadodara", state="Gujarat", latitude=22.3, longitude=73.2)
    farm2 = Farm(id=2, user_id=test_user.id, farm_name="Anand Farm", district="Anand", state="Gujarat", latitude=22.5, longitude=72.9)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1, farm2]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    res = FarmContextResolver.resolve(db=mock_db, user=test_user, requested_farm_id=None, query="What's the weather at my Anand farm?")
    assert res.status == FarmResolutionStatus.RESOLVED
    assert res.context.farm_id == 2
    assert res.context.district == "Anand"


def test_user_with_no_farm(test_user, mock_db):
    """Verify that a user with 0 farms is notified to add a farm."""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None

    res = FarmContextResolver.resolve(db=mock_db, user=test_user)
    assert res.status == FarmResolutionStatus.NO_FARM
    assert "add a farm" in res.message.lower()


# ---------------------------------------------------------------------------
# TEST GROUP 4: END-TO-END ORCHESTRATOR & ZERO GENERIC ADVICE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_weather_flow_no_generic_advice(test_user, mock_db):
    """
    PRIMARY ACCEPTANCE TEST:
    Verify that "Give me weather updates for my farm":
    1. Identifies intent = WEATHER
    2. Calls WeatherAgent and get_farm_weather
    3. Returns weather-focused response
    4. Absolutely NO generic advice (NPK, soil testing, seeds, drip irrigation, mandi prices)
    """
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="Test Farm", district="Anand", state="Gujarat", latitude=22.56, longitude=72.95)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Mock tool execution to simulate live weather snapshot
    with patch.object(tool_registry, "execute_tool") as mock_exec:
        from farmxpert.services.orchestrator.tool_registry import ToolExecutionResult
        mock_exec.return_value = ToolExecutionResult(
            tool_name="get_farm_weather",
            success=True,
            data={
                "location": {"name": "Test Farm", "latitude": 22.56, "longitude": 72.95},
                "current": {
                    "temperature_c": 31.0,
                    "humidity_percent": 64,
                    "rain_probability_percent": 35,
                    "rainfall_mm": 4.2,
                    "wind_speed_kmh": 12.0,
                    "condition": "scattered clouds"
                },
                "forecast": []
            },
            duration_ms=45.0
        )

        response = await farmxpert_orchestrator.process_request(
            message="Give me weather updates for my farm",
            user=test_user,
            db=mock_db,
            session_id="test_session"
        )

        assert response["success"] is True
        assert response["intent"] == "WEATHER"
        assert response["agent"] == "WeatherAgent"
        assert len(response["tool_calls"]) == 1
        assert response["tool_calls"][0]["tool"] == "get_farm_weather"

        resp_text = response["response"].lower()

        # Must have weather info
        assert "31" in resp_text or "temperature" in resp_text or "weather" in resp_text

        # Must NOT contain generic farming advice
        forbidden_terms = [
            "conduct a soil test",
            "balanced n-p-k",
            "implement precision drip",
            "certified disease-resistant seed",
            "monitor daily apmc mandi",
            "avoid over-application of synthetic nitrogen",
            "always verify mandi modal prices"
        ]
        for term in forbidden_terms:
            assert term not in resp_text, f"Forbidden generic advice term found in weather response: {term}"


@pytest.mark.asyncio
async def test_orchestrator_market_does_not_call_weather(test_user, mock_db):
    """Verify that a market query executes market tools and does NOT call weather tools."""
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="Test Farm", district="Anand", state="Gujarat", latitude=22.56, longitude=72.95)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = await farmxpert_orchestrator.process_request(
        message="What is the mandi price of cotton?",
        user=test_user,
        db=mock_db,
        session_id="test_session"
    )

    assert response["intent"] == "MARKET_PRICES"
    assert response["agent"] == "MarketIntelligenceAgent"
    tool_names = [tc["tool"] for tc in response["tool_calls"]]
    assert "get_farm_weather" not in tool_names


@pytest.mark.asyncio
async def test_orchestrator_weather_failure_handled_cleanly(test_user, mock_db):
    """Verify that if weather API fails, clean error is returned without substituting generic advice."""
    farm1 = Farm(id=1, user_id=test_user.id, farm_name="Test Farm", district="Anand", state="Gujarat", latitude=22.56, longitude=72.95)
    mock_db.query.return_value.filter.return_value.all.return_value = [farm1]
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(tool_registry, "execute_tool") as mock_exec:
        from farmxpert.services.orchestrator.tool_registry import ToolExecutionResult
        mock_exec.return_value = ToolExecutionResult(
            tool_name="get_farm_weather",
            success=False,
            data={},
            error="The weather service is temporarily unavailable for your farm. Please try again shortly.",
            duration_ms=10.0
        )

        response = await farmxpert_orchestrator.process_request(
            message="Give me weather updates for my farm",
            user=test_user,
            db=mock_db,
            session_id="test_session"
        )

        assert "temporarily unavailable" in response["response"]
        # Must not have substituted generic farming advice
        assert "soil test" not in response["response"].lower()
        assert "drip irrigation" not in response["response"].lower()
        assert "npk" not in response["response"].lower()
