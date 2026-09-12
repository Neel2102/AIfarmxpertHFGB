"""
Comprehensive Automated Test Suite for Smart Chat & Orchestrator Real Failures
Verifies all 6 real conversation scenarios:
- Test A: Profit Optimization Plan ("give me a plan to get my maximum profit")
- Test B: Crop Recommendation Completion ("which crop should i plant on my farm")
- Test C: Plant Image / Disease Upload Flow (multipart image request -> vision diagnosis)
- Test D: Weather + Irrigation Multi-Intent ("what is the weather update should i irrigate or not today")
- Test E: Location Context Extraction ("i am in ahmedabad")
- Test F: Session Context Retention & Follow-up ("which crop should i plant?" retains Ahmedabad)
"""

import sys
import os
import io
import pytest
from unittest.mock import MagicMock
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Crop, SoilTest
from farmxpert.services.orchestrator.farmxpert_orchestrator import farmxpert_orchestrator
from farmxpert.services.orchestrator.intent_router import intent_router, IntentType
from farmxpert.interfaces.api.routes.chat_routes import chat_vision
from fastapi import UploadFile


@pytest.fixture
def sample_farmer():
    return User(
        id=202,
        username="farmer_patel",
        email="patel@farmxpert.test",
        full_name="Bhavesh Patel",
        is_active=True
    )


@pytest.fixture
def mock_db_with_farm(sample_farmer):
    db = MagicMock()
    farm = Farm(
        id=10,
        user_id=sample_farmer.id,
        farm_name="Bhavesh Patel Agro Farm",
        name="Bhavesh Patel Agro Farm",
        district="Rajkot",
        state="Gujarat",
        soil_type="Black Soil",
        size_acres=10.0,
        latitude=22.30,
        longitude=70.80,
        location="Rajkot, Gujarat"
    )
    crop = Crop(
        id=10,
        farm_id=10,
        crop_type="Cotton",
        variety="BT-6",
        area_acres=10.0
    )
    db.query.return_value.filter.return_value.all.return_value = [farm]
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.order_by.return_value.first.return_value = None
    return db


@pytest.fixture
def mock_db_empty(sample_farmer):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    return db


# ===========================================================================
# TEST A: PROFIT OPTIMIZATION
# ===========================================================================

@pytest.mark.asyncio
async def test_a_profit_optimization_intent_and_data(sample_farmer, mock_db_with_farm):
    """
    User: 'give me a plan to get my maximum profit'
    Expected:
    - Intent: PROFIT_OPTIMIZATION
    - Uses farm acreage (10 acres) and APMC mandi benchmarks
    - Returns structured agronomic revenue, costs, and net margin
    - No generic ChatGPT-style filler
    """
    res = await farmxpert_orchestrator.process_request(
        message="give me a plan to get my maximum profit",
        user=sample_farmer,
        db=mock_db_with_farm,
        session_id="test_session_profit"
    )

    assert res["success"] is True
    assert res["intent"] == "PROFIT_OPTIMIZATION"
    assert res["agent"] == "ProfitOptimizationAgent"
    
    resp_text = res["response"]
    assert "Profit Optimization" in resp_text or "Profit" in resp_text
    # Verify presence of quantitative economic calculations
    assert "Cotton" in resp_text or "Groundnut" in resp_text
    assert "₹" in resp_text
    assert "Acre" in resp_text or "acre" in resp_text
    # Verify no generic ChatGPT filler phrases
    assert "1. Analyze current crop/livestock performance" not in resp_text


# ===========================================================================
# TEST B: CROP RECOMMENDATION
# ===========================================================================

@pytest.mark.asyncio
async def test_b_crop_recommendation_flow(sample_farmer, mock_db_with_farm):
    """
    User: 'which crop should i plant on my farm'
    Expected:
    - Intent: CROP_SELECTION
    - Uses farm soil type ('Black Soil') and location ('Rajkot, Gujarat')
    - Returns concrete crop options (Cotton, Groundnut, etc.)
    - Does not ask for details already present on the farm
    """
    res = await farmxpert_orchestrator.process_request(
        message="which crop should i plant on my farm",
        user=sample_farmer,
        db=mock_db_with_farm,
        session_id="test_session_crop"
    )

    assert res["success"] is True
    assert res["intent"] == "CROP_SELECTION"
    assert res["agent"] == "CropSelectorAgent"
    
    resp_text = res["response"]
    # Check that recommendation mentions suitable crops and soil
    assert "Cotton" in resp_text or "Groundnut" in resp_text
    assert "Black" in resp_text or "Soil" in resp_text or "soil" in resp_text


# ===========================================================================
# TEST C: PLANT IMAGE / DISEASE VISION REQUEST
# ===========================================================================

@pytest.mark.asyncio
async def test_c_image_disease_diagnostic_never_500(sample_farmer):
    """
    User uploads an image: 'what is this how to get rid of this from my plants'
    Expected:
    - HTTP 200 response (never 500 'Farm orchestrator unavailable')
    - Diagnosis, confidence, symptoms, causes, treatments, and prevention
    - Uncertainty notice that visual diagnosis cannot guarantee 100% confirmation
    """
    # Create a dummy image file (1x1 pixel PNG bytes)
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    
    upload_file = UploadFile(
        filename="infected_leaf.png",
        file=io.BytesIO(png_bytes),
        headers={"content-type": "image/png"}
    )

    result = await chat_vision(
        current_user=sample_farmer,
        file=upload_file,
        prompt="what is this how to get rid of this from my plants",
        session_id="test_vision_session"
    )

    assert result["success"] is True
    assert "vision_result" in result
    vr = result["vision_result"]
    assert "diagnosis" in vr
    assert "recommended_treatment" in vr
    assert len(vr["recommended_treatment"]) > 0

    resp_text = result["response"]
    # Verify diagnostic report formatting
    assert "Diagnostic Report" in resp_text or "Diagnosis" in resp_text
    assert "Recommended Treatments" in resp_text or "treatment" in resp_text.lower()
    assert "Notice" in resp_text or "Warning" in resp_text or "KVK" in resp_text


# ===========================================================================
# TEST D: WEATHER + IRRIGATION MULTI-INTENT
# ===========================================================================

@pytest.mark.asyncio
async def test_d_weather_plus_irrigation_multi_intent(sample_farmer, mock_db_with_farm):
    """
    User: 'what is the weather update should i irrigate or not today'
    Expected:
    - Decomposes into WEATHER + IRRIGATION
    - Provides weather status
    - Provides irrigation guidance based on rainfall probability & soil moisture
    - Does not reject request because of single-intent routing
    """
    res = await farmxpert_orchestrator.process_request(
        message="what is the weather update should i irrigate or not today",
        user=sample_farmer,
        db=mock_db_with_farm,
        session_id="test_session_weather_irrigation"
    )

    assert res["success"] is True
    assert res["intent"] == "WEATHER"
    
    resp_text = res["response"]
    # Must contain both weather information and irrigation recommendation
    assert "Weather" in resp_text or "Temperature" in resp_text or "°C" in resp_text
    assert "Irrigation" in resp_text or "irrigate" in resp_text.lower()


# ===========================================================================
# TEST E: LOCATION CONTEXT EXTRACTION & CLEAN OUTPUT
# ===========================================================================

@pytest.mark.asyncio
async def test_e_location_context_extraction(sample_farmer, mock_db_empty):
    """
    User: 'i am in ahmedabad'
    Expected:
    - Intent: LOCATION_UPDATE
    - Stores 'Ahmedabad' in session memory
    - Warm conversational acknowledgment
    - NO malformed tokens like '? Yes.', 'Next Steps:', or prompt engineering artifacts
    """
    session_id = "shared_session_ahmedabad_101"
    res = await farmxpert_orchestrator.process_request(
        message="i am in ahmedabad",
        user=sample_farmer,
        db=mock_db_empty,
        session_id=session_id
    )

    assert res["success"] is True
    assert res["intent"] == "LOCATION_UPDATE"

    resp_text = res["response"]
    assert "Ahmedabad" in resp_text
    # Strictly verify absence of prompt-template leakage
    assert "? Yes." not in resp_text
    assert "`Next Steps:`" not in resp_text
    assert "Direct Answer:" not in resp_text

    # Verify session memory captured Ahmedabad
    assert session_id in farmxpert_orchestrator.conversation_memory
    assert farmxpert_orchestrator.conversation_memory[session_id].get("location") == "Ahmedabad"


# ===========================================================================
# TEST F: SESSION CONTEXT RETENTION
# ===========================================================================

@pytest.mark.asyncio
async def test_f_session_context_retention(sample_farmer, mock_db_empty):
    """
    Follow-up in the same session:
    User: 'which crop should i plant?'
    Expected:
    - Uses 'Ahmedabad' stored from previous turn
    - Executes crop recommendation workflow for Ahmedabad
    - Does NOT ask user again for location!
    """
    session_id = "shared_session_ahmedabad_101"  # Same session from Test E

    res = await farmxpert_orchestrator.process_request(
        message="which crop should i plant?",
        user=sample_farmer,
        db=mock_db_empty,
        session_id=session_id
    )

    assert res["success"] is True
    assert res["intent"] == "CROP_SELECTION"
    
    resp_text = res["response"]
    # Retains Ahmedabad in recommendation without asking user for location again
    assert "Ahmedabad" in resp_text
    assert "Cotton" in resp_text or "Groundnut" in resp_text or "Soybean" in resp_text
