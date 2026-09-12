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
from farmxpert.models.user_models import User
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/soil-tests", tags=["Soil Tests"])
logger = get_logger("soil_tests_api")


# ── Schemas ────────────────────────────────────────────────

class SoilTestCreate(BaseModel):
    farm_id: Optional[int] = None
    user_id: Optional[int] = None
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
#
# Every endpoint here is scoped to the authenticated farmer. They previously
# accepted an optional user_id/farm_id query parameter and otherwise fell back
# to `db.query(Farm).first()`, which served the first farm in the table to every
# caller — one farmer's soil data shown to another, with no login required.


def _require_own_farm(db: Session, current_user: User) -> Farm:
    """Return the caller's own farm, or 404. Never another farmer's."""
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(
            status_code=404,
            detail="No farm configured yet. Add your farm details in Settings first.",
        )
    return farm


@router.post("/save")
async def save_soil_test(
    req: SoilTestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a soil test reading against the authenticated farmer's own farm."""
    farm = _require_own_farm(db, current_user)
    try:
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
        logger.info("Soil test saved: id=%s farm=%s", test.id, farm.id)
        return {"success": True, "message": "Soil test saved.", "id": test.id}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Failed to save soil test for user_id=%s", current_user.id)
        raise HTTPException(status_code=500, detail="We couldn't save this soil reading.")


@router.get("/list")
async def list_soil_tests(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated soil test history for the caller's own farm (newest first)."""
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        return {"tests": [], "count": 0, "offset": offset, "limit": limit}

    tests = (
        db.query(SoilTest)
        .filter(SoilTest.farm_id == farm.id)
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
async def latest_soil_test(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Most recent soil test for the caller's own farm."""
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        return {"has_data": False, "message": "No farm configured yet."}

    test = (
        db.query(SoilTest)
        .filter(SoilTest.farm_id == farm.id)
        .order_by(SoilTest.test_date.desc())
        .first()
    )
    if not test:
        return {"has_data": False, "message": "No soil tests recorded yet."}
    return {"has_data": True, "test": _to_response(test)}


@router.get("/farm-info")
async def get_farm_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The caller's own farm record."""
    farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()
    if not farm:
        return {"has_farm": False}
    return {
        "has_farm": True,
        "farm": {
            "id": farm.id,
            "name": farm.farm_name,
            "farmer_name": farm.farmer_name,
            "farmer_phone": farm.farmer_phone,
            "farmer_email": farm.farmer_email,
            "location": farm.location,
            "size_acres": float(farm.size_acres) if farm.size_acres is not None else None,
            "latitude": float(farm.latitude) if farm.latitude is not None else None,
            "longitude": float(farm.longitude) if farm.longitude is not None else None,
            "soil_type": farm.soil_type,
            "crop_type": farm.crop_type,
        },
    }


@router.get("/live")
async def get_live_soil_telemetry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Live soil telemetry.

    Delegates to the one canonical telemetry service so this endpoint, the
    Hardware IoT page and the Soil & Sensors page can never disagree. Kept as an
    alias for existing callers; /api/blynk/telemetry/live is the primary route.
    """
    from farmxpert.services.telemetry_service import get_live_telemetry
    from farmxpert.config.settings import settings

    try:
        return await get_live_telemetry(
            db, current_user.id, settings.blynk_base_url or "https://blr1.blynk.cloud"
        )
    except Exception:
        logger.exception("Live soil telemetry failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=503, detail="Live sensor data is temporarily unavailable.")
