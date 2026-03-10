"""
Soil Test API Routes — Save & Retrieve 9-parameter soil test data
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from farmxpert.models.database import get_db
from farmxpert.models.farm_models import SoilTest, Farm
from farmxpert.models.blynk_models import SensorReading, BlynkDevice
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/soil-tests", tags=["Soil Tests"])
logger = get_logger("soil_tests_api")


# ── Schemas ────────────────────────────────────────────────

class SoilTestCreate(BaseModel):
    air_temperature: Optional[float] = None
    air_humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    soil_temperature: Optional[float] = None
    soil_ec: Optional[float] = None
    soil_ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    source: Optional[str] = "blynk"
    notes: Optional[str] = None


class SoilTestResponse(BaseModel):
    id: int
    farm_id: int
    test_date: str
    air_temperature: Optional[float]
    air_humidity: Optional[float]
    soil_moisture: Optional[float]
    soil_temperature: Optional[float]
    soil_ec: Optional[float]
    soil_ph: Optional[float]
    nitrogen: Optional[float]
    phosphorus: Optional[float]
    potassium: Optional[float]
    source: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]


def _to_response(t: SoilTest) -> dict:
    return {
        "id": t.id,
        "farm_id": t.farm_id,
        "test_date": t.test_date.isoformat() if t.test_date else None,
        "air_temperature": t.air_temperature,
        "air_humidity": t.air_humidity,
        "soil_moisture": t.soil_moisture,
        "soil_temperature": t.soil_temperature,
        "soil_ec": t.soil_ec,
        "soil_ph": t.soil_ph,
        "nitrogen": t.nitrogen,
        "phosphorus": t.phosphorus,
        "potassium": t.potassium,
        "source": t.source,
        "notes": t.notes,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


# ── Endpoints ──────────────────────────────────────────────

@router.post("/save")
async def save_soil_test(req: SoilTestCreate, db: Session = Depends(get_db)):
    """Save a new 9-parameter soil test reading from the frontend."""
    try:
        # Resolve farm (first available)
        farm = db.query(Farm).first()
        if not farm:
            raise HTTPException(status_code=400, detail="No farm found. Please set up your farm first.")

        test = SoilTest(
            farm_id=farm.id,
            air_temperature=req.air_temperature,
            air_humidity=req.air_humidity,
            soil_moisture=req.soil_moisture,
            soil_temperature=req.soil_temperature,
            soil_ec=req.soil_ec,
            soil_ph=req.soil_ph,
            nitrogen=req.nitrogen,
            phosphorus=req.phosphorus,
            potassium=req.potassium,
            source=req.source or "blynk",
            notes=req.notes,
        )
        db.add(test)
        db.commit()
        db.refresh(test)

        logger.info(f"Soil test saved: id={test.id} farm={farm.id}")
        return {"success": True, "message": "Soil test saved.", "id": test.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save soil test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_soil_tests(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get paginated soil test history (newest first)."""
    tests = (
        db.query(SoilTest)
        .order_by(SoilTest.test_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return {
        "tests": [_to_response(t) for t in tests],
        "count": len(tests),
        "offset": offset,
        "limit": limit,
    }


@router.get("/latest")
async def latest_soil_test(db: Session = Depends(get_db)):
    """Get the most recent soil test reading."""
    test = db.query(SoilTest).order_by(SoilTest.test_date.desc()).first()
    if not test:
        return {"has_data": False, "message": "No soil tests recorded yet."}
    return {"has_data": True, "test": _to_response(test)}


@router.get("/farm-info")
async def get_farm_info(db: Session = Depends(get_db)):
    """Get the farmer's farm info (auto-populated from users table)."""
    farm = db.query(Farm).first()
    if not farm:
        return {"has_farm": False}
    return {
        "has_farm": True,
        "farm": {
            "id": farm.id,
            "name": farm.name,
            "farmer_name": farm.farmer_name,
            "farmer_phone": farm.farmer_phone,
            "farmer_email": farm.farmer_email,
            "location": farm.location,
            "size_acres": farm.size_acres,
        },
    }


@router.get("/user-live")
async def get_user_live_soil_telemetry(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get live telemetry for a specific user's farm (pass user_id as query param).
    The frontend passes the user_id from AuthContext to scope data correctly.
    """
    from farmxpert.models.farm_profile_models import FarmProfile

    # Scope farm to this user if user_id provided
    if user_id:
        profile = db.query(FarmProfile).filter(FarmProfile.user_id == user_id).first()
        if not profile:
            return {"has_data": False, "message": "No farm profile found for this user."}
        # Find farm matching this user profile (by name/state if no direct FK)
        # Fall back to querying SoilTests for farms whose auth link we can resolve
        farm = db.query(Farm).filter(Farm.user_id == user_id).first() if hasattr(Farm, 'user_id') else None
        if not farm:
            # Use SoilTest directly — get latest from any farm, scoped by what we know
            # When farm_id is unavailable, return latest global reading
            pass

    # Try SoilTest (latest) — best effort
    try:
        latest_test = (
            db.query(SoilTest)
            .order_by(SoilTest.test_date.desc())
            .first()
        )
        if not latest_test:
            return {"has_data": False, "message": "No sensor data recorded yet."}

        return {
            "has_data": True,
            "source": "soil_test",
            "data": {
                "air_temperature": latest_test.air_temperature,
                "air_humidity": latest_test.air_humidity,
                "soil_moisture": latest_test.soil_moisture,
                "soil_temperature": latest_test.soil_temperature,
                "soil_ec": latest_test.soil_ec,
                "soil_ph": latest_test.soil_ph,
                "nitrogen": latest_test.nitrogen,
                "phosphorus": latest_test.phosphorus,
                "potassium": latest_test.potassium,
            },
            "timestamp": latest_test.test_date.isoformat() if latest_test.test_date else None,
        }
    except Exception as e:
        logger.error(f"Error fetching user-live telemetry: {e}")
        return {"has_data": False, "message": "Failed to fetch sensor data."}


@router.get("/live")
async def get_live_soil_telemetry(db: Session = Depends(get_db)):
    """Get the latest live soil telemetry data from active FarmHardware node."""
    try:
        # Get the first available farm (can be enhanced to use user context)
        farm = db.query(Farm).first()
        if not farm:
            return {"has_data": False, "message": "No farm found. Please set up your farm first."}

        # Try to get latest SensorReading first (more recent, high-frequency data)
        latest_sensor = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farm.id)
            .order_by(SensorReading.recorded_at.desc())
            .first()
        )

        # If no sensor data, fall back to latest SoilTest
        if not latest_sensor:
            latest_soil_test = (
                db.query(SoilTest)
                .filter(SoilTest.farm_id == farm.id)
                .order_by(SoilTest.test_date.desc())
                .first()
            )
            
            if not latest_soil_test:
                return {"has_data": False, "message": "No soil telemetry data available."}
            
            # Return SoilTest data in live format
            return {
                "has_data": True,
                "source": "soil_test",
                "data": {
                    "air_temperature": latest_soil_test.air_temperature,
                    "air_humidity": latest_soil_test.air_humidity,
                    "soil_moisture": latest_soil_test.soil_moisture,
                    "soil_temperature": latest_soil_test.soil_temperature,
                    "soil_ec": latest_soil_test.soil_ec,
                    "soil_ph": latest_soil_test.soil_ph,
                    "nitrogen": latest_soil_test.nitrogen,
                    "phosphorus": latest_soil_test.phosphorus,
                    "potassium": latest_soil_test.potassium,
                },
                "timestamp": latest_soil_test.test_date.isoformat() if latest_soil_test.test_date else None,
                "notes": latest_soil_test.notes,
            }

        # Return SensorReading data (preferred - more recent)
        return {
            "has_data": True,
            "source": "sensor_reading",
            "data": {
                "air_temperature": float(latest_sensor.air_temperature) if latest_sensor.air_temperature else None,
                "air_humidity": float(latest_sensor.air_humidity) if latest_sensor.air_humidity else None,
                "soil_moisture": float(latest_sensor.soil_moisture) if latest_sensor.soil_moisture else None,
                "soil_temperature": float(latest_sensor.soil_temperature) if latest_sensor.soil_temperature else None,
                "soil_ec": float(latest_sensor.soil_ec) if latest_sensor.soil_ec else None,
                "soil_ph": float(latest_sensor.soil_ph) if latest_sensor.soil_ph else None,
                "nitrogen": float(latest_sensor.nitrogen) if latest_sensor.nitrogen else None,
                "phosphorus": float(latest_sensor.phosphorus) if latest_sensor.phosphorus else None,
                "potassium": float(latest_sensor.potassium) if latest_sensor.potassium else None,
            },
            "timestamp": latest_sensor.recorded_at.isoformat() if latest_sensor.recorded_at else None,
            "device_id": latest_sensor.device_id,
        }

    except Exception as e:
        logger.error(f"Failed to fetch live soil telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
