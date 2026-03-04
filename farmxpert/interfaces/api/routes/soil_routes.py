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
