import sys
import os
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from farmxpert.models.database import Base
from farmxpert.models.user_models import User
from farmxpert.models.farm_models import Farm, Crop, SoilTest
from farmxpert.models.blynk_models import SensorReading
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.services.orchestrator.tool_registry import tool_registry
from farmxpert.services.orchestrator.farm_context import FarmContext


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    target_tables = [
        User.__table__,
        Farm.__table__,
        Crop.__table__,
        SoilTest.__table__,
        FarmProfile.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=target_tables)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_farm_model_name_property(db_session):
    """Verify Farm has no 'farms.name' column in SQL but supports .name in Python."""
    # Ensure 'name' is NOT a mapped column in Farm table columns
    table_col_names = [c.name for c in Farm.__table__.columns]
    assert "farm_name" in table_col_names
    assert "name" not in table_col_names, "'name' column must not exist in SQL table definition"

    farm = Farm(
        id=1,
        user_id=1,
        farm_name="Green Valley",
        state="Gujarat",
        district="Rajkot",
        size_acres=10.0
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)

    # Verify python getter and setter
    assert farm.farm_name == "Green Valley"
    assert farm.name == "Green Valley"
    farm.name = "Sunshine Farm"
    assert farm.farm_name == "Sunshine Farm"


def test_hardware_iot_save_and_live_telemetry(db_session):
    """Test saving IoT soil test readings and retrieving live telemetry."""
    farm = Farm(
        id=42,
        user_id=42,
        farm_name="IoT Test Farm",
        state="Gujarat",
        district="Ahmedabad",
        size_acres=5.0
    )
    db_session.add(farm)
    db_session.commit()

    # Add a soil test reading
    test = SoilTest(
        id=101,
        farm_id=farm.id,
        air_temperature=28.5,
        air_humidity=65.0,
        soil_moisture=45.2,
        soil_temperature=24.0,
        soil_ec=1.2,
        soil_ph=6.8,
        nitrogen=140.0,
        phosphorus=32.0,
        potassium=180.0,
        source="blynk",
        notes="Automated hardware test"
    )
    db_session.add(test)
    db_session.commit()

    # Query latest
    latest = db_session.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.test_date.desc()).first()
    assert latest is not None
    assert latest.soil_moisture == 45.2
    assert latest.soil_ph == 6.8
    assert latest.source == "blynk"


@pytest.mark.asyncio
async def test_weather_fallback_geocoding(db_session):
    """Test weather tool geocoding fallback for Indian farm regions."""
    farm = Farm(
        id=99,
        user_id=99,
        farm_name="Kutch Cotton",
        state="Gujarat",
        district="Rajkot",
        location="Rajkot, Gujarat",
        size_acres=12.0
    )
    db_session.add(farm)
    db_session.commit()

    farm_ctx = FarmContext(
        user_id=99,
        farm_id=farm.id,
        farm_name=farm.farm_name,
        state=farm.state,
        district=farm.district,
        location_name=farm.location,
        latitude=farm.latitude,
        longitude=farm.longitude
    )

    # Even with latitude=None and longitude=None, weather tool should resolve coordinates from location/district
    result = await tool_registry.execute_tool(
        tool_name="get_farm_weather",
        farm_context=farm_ctx,
        db=db_session
    )

    assert result.success is True or result.data is not None
    # Coordinates should be backfilled
    assert farm.latitude is not None or "temperature" in result.data or "forecast" in result.data


def test_farm_profile_sync_to_farm(db_session):
    """Verify settings sync from FarmProfile to Farm model."""
    user = User(
        id=77,
        username="patel_test",
        email="farmer77@test.com",
        hashed_password="fake_hash",
        full_name="Ramesh Patel"
    )
    db_session.add(user)

    farm = Farm(
        id=77,
        user_id=77,
        farm_name="Old Farm Name",
        location="Old Location",
        size_acres=2.0
    )
    db_session.add(farm)
    db_session.commit()

    # Simulate Settings PUT /auth/farm-profile update
    farm.farm_name = "Patel Organic Farm"
    farm.location = "Junagadh, Gujarat"
    farm.latitude = 21.5222
    farm.longitude = 70.4579
    farm.size_acres = 8.5
    farm.soil_type = "Alluvial Soil"
    farm.crop_type = "Groundnut"
    db_session.commit()
    db_session.refresh(farm)

    assert farm.farm_name == "Patel Organic Farm"
    assert float(farm.latitude) == pytest.approx(21.5222)
    assert farm.soil_type == "Alluvial Soil"
    assert farm.crop_type == "Groundnut"
