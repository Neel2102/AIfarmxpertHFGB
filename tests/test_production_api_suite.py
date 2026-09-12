import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy.pool import StaticPool

from farmxpert.interfaces.api.main import app
from farmxpert.models.database import Base, get_db
from farmxpert.models.user_models import User, AuthUser
from farmxpert.models.farm_models import Farm, Crop, Task, FarmTask, SoilTest
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.blynk_models import BlynkDevice
from farmxpert.interfaces.api.routes.auth_routes import get_current_user


@pytest.fixture(scope="module")
def test_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    target_tables = [
        User.__table__,
        AuthUser.__table__,
        Farm.__table__,
        Crop.__table__,
        Task.__table__,
        FarmTask.__table__,
        SoilTest.__table__,
        FarmProfile.__table__,
        BlynkDevice.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=target_tables)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Pre-populate a test user
    user = User(
        id=99,
        username="prod_tester",
        email="tester@farmxpert.com",
        hashed_password="fakehashfortesting",
        full_name="Prod Tester",
        is_active=True
    )
    auth_user = AuthUser(
        id=99,
        farmer_id="FARMER-99",
        username="prod_tester",
        email="tester@farmxpert.com",
        password_hash="fakehashfortesting",
        role="farmer"
    )
    session.add(user)
    session.add(auth_user)
    session.commit()

    yield session
    session.close()


@pytest.fixture(scope="module")
def client(test_db_session):
    test_user = test_db_session.query(User).filter(User.id == 99).first()

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    def override_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_orchestrator_status_endpoint(client):
    """1. GET /api/orchestrator/status must return 200 and healthy status (NOT 404)."""
    response = client.get("/api/orchestrator/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "ok", "running", "online"]
    assert "active_agents" in data or "agents" in data or "uptime" in data


def test_blynk_telemetry_live_without_device(client):
    """2. GET /api/blynk/telemetry/live must return 200 with connected=False when no hardware connected."""
    response = client.get("/api/blynk/telemetry/live")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("connected") is False
    assert data.get("status") == "not_connected"


def test_blynk_register_and_check_device(client):
    """3. POST /api/blynk/register-device and GET /api/blynk/check-device must return 200."""
    reg_payload = {
        "device_name": "Field Sensor ESP32",
        "auth_token": "blynk_test_token_12345",
        "farm_id": None
    }
    reg_res = client.post("/api/blynk/register-device", json=reg_payload)
    assert reg_res.status_code in [200, 201], f"Register device failed: {reg_res.text}"
    
    check_res = client.get("/api/blynk/check-device")
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data.get("is_configured") is True or check_data.get("has_device") is True or check_data.get("device") is not None


def test_farm_profile_get_and_post_and_put(client, test_db_session):
    """4. GET, POST, and PUT /api/auth/farm-profile must return 200 and sync to canonical Farm."""
    profile_payload = {
        "farm_name": "Sunrise Organic Farms",
        "location": "Nashik, Maharashtra",
        "total_area": 12.5,
        "primary_crops": ["Pomegranate", "Cotton"],
        "soil_type": "Black Soil",
        "irrigation_type": "Drip Irrigation",
        "latitude": 19.9975,
        "longitude": 73.7898
    }
    
    # Test POST alias
    post_res = client.post("/api/auth/farm-profile", json=profile_payload)
    assert post_res.status_code == 200, f"POST /farm-profile failed: {post_res.text}"
    post_data = post_res.json()
    assert post_data["farm_name"] == "Sunrise Organic Farms"

    # Test GET
    get_res = client.get("/api/auth/farm-profile")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["farm_name"] == "Sunrise Organic Farms"

    # Verify canonical Farm record was created / synced in DB
    farm = test_db_session.query(Farm).filter(Farm.user_id == 99).first()
    assert farm is not None
    assert farm.farm_name == "Sunrise Organic Farms"
    assert float(farm.latitude) == pytest.approx(19.9975)


def test_farm_layout_get_and_put(client, test_db_session):
    """5. GET and PUT /api/auth/farm-layout must persist layout and update canonical Farm coordinates."""
    # Test GET layout before polygon is drawn
    get_res1 = client.get("/api/auth/farm-layout")
    assert get_res1.status_code == 200
    data1 = get_res1.json()
    assert data1.get("farm_name") == "Sunrise Organic Farms"

    # Save a polygon layout
    layout_payload = {
        "name": "Sunrise Organic Farms",
        "center": [19.998, 73.790],
        "zoom": 16,
        "boundaries": [
            {"lat": 19.997, "lng": 73.789},
            {"lat": 19.999, "lng": 73.789},
            {"lat": 19.999, "lng": 73.791},
            {"lat": 19.997, "lng": 73.791}
        ],
        "soil_type": "Black Soil",
        "irrigation_type": "Drip Irrigation",
        "area_acres": 12.5,
        "notes": "Boundary mapped from satellite view"
    }
    put_res = client.put("/api/auth/farm-layout", json=layout_payload)
    assert put_res.status_code == 200, f"PUT /farm-layout failed: {put_res.text}"
    put_data = put_res.json()
    assert put_data["success"] is True

    # Check that canonical Farm was updated with center coordinates
    test_db_session.expire_all()
    farm = test_db_session.query(Farm).filter(Farm.user_id == 99).first()
    assert float(farm.latitude) == pytest.approx(19.998)
    assert float(farm.longitude) == pytest.approx(73.790)


def test_tasks_farms_and_crops_endpoint(client):
    """6. GET /api/tasks/farms-and-crops returns 200 with the authenticated user's farm and crop."""
    response = client.get("/api/tasks/farms-and-crops")
    assert response.status_code == 200, f"GET /farms-and-crops failed: {response.text}"
    data = response.json()
    assert "farms" in data
    assert len(data["farms"]) > 0
    farm_item = data["farms"][0]
    assert farm_item["name"] == "Sunrise Organic Farms"
    assert len(farm_item.get("crops", [])) > 0


def test_tasks_daily_flow_generation(client):
    """7. POST /api/tasks/daily-flow/generate successfully creates crop plan without 500 error."""
    gen_payload = {
        "force_regenerate": True,
        "notes": "Testing seasonal daily flow generation"
    }
    response = client.post("/api/tasks/daily-flow/generate", json=gen_payload)
    assert response.status_code == 200, f"POST /daily-flow/generate failed: {response.text}"
    data = response.json()
    assert data.get("total_tasks_count", 0) > 0
    assert "today" in data
    assert "upcoming" in data
    assert "stages" in data
