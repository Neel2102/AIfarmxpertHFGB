import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from farmxpert.interfaces.api.main import app
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.models.user_models import User

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_auth():
    test_user = User(
        id=1,
        username="testfarmer",
        email="testfarmer@example.com",
        is_active=True
    )
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_api_chat_weather_endpoint():
    # Test POST /api/chat with weather query
    payload = {
        "message": "Give me weather updates for my farm",
        "farm_id": 1,
        "chat_history": []
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200, f"Failed with {response.status_code}: {response.text}"
    data = response.json()
    assert "response" in data
    assert "intent" in data or "metadata" in data
    text = data.get("response", "").lower()
    # Ensure zero generic unsolicited advice
    assert "certified seeds" not in text
    assert "npk" not in text
    assert "soil testing" not in text

def test_api_chat_orchestrate_endpoint():
    payload = {
        "message": "What is the current temperature and humidity on my farm?",
        "farm_id": 1,
        "chat_history": []
    }
    response = client.post("/api/chat/orchestrate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("intent") == "WEATHER"
    assert len(data.get("tool_calls", [])) > 0
    assert data["tool_calls"][0]["tool"] == "get_farm_weather"

def test_api_chat_debug_endpoint():
    response = client.get("/api/chat/debug?query=Give%20me%20weather%20updates")
    assert response.status_code == 200
    data = response.json()
    assert data.get("user_request") == "Give me weather updates"
    assert data.get("resolved_intent") == "WEATHER"
    assert "tools_executed" in data

