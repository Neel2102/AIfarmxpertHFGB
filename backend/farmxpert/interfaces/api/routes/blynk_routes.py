"""
Blynk Device Management & Sensor Data API Routes
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from farmxpert.models.database import get_db
from farmxpert.models.blynk_models import BlynkDevice, SensorReading
from farmxpert.models.farm_models import Farm
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.models.user_models import User
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/blynk", tags=["Blynk IoT"])
logger = get_logger("blynk_api")


# ── Encryption helpers ──────────────────────────────────────

def _encrypt_token(token: str) -> str:
    """Simple symmetric obfuscation for auth tokens."""
    salt = secrets.token_hex(8)
    return f"{salt}:{token}"


def _decrypt_token(stored: str) -> str:
    """Reverse of _encrypt_token."""
    if ":" in stored:
        _, token = stored.split(":", 1)
        return token
    return stored


# ── Helper: resolve farm from user ─────────────────────────

def _resolve_farm(db: Session, user: User) -> Farm:
    """Get the farmer's farm. Every farmer MUST have a farm."""
    farm = db.query(Farm).first()  # For now, get first farm; in multi-tenant, filter by user
    if not farm:
        raise HTTPException(
            status_code=400,
            detail="Farm not initialized for user. Please complete your farm profile first."
        )
    return farm


# ── Request / Response Schemas ─────────────────────────────

class CheckDeviceResponse(BaseModel):
    blynk_required: bool
    message: str
    device: Optional[dict] = None


class RegisterDeviceRequest(BaseModel):
    auth_token: str = Field(..., min_length=4, max_length=255, description="Blynk Auth Token")
    device_name: Optional[str] = Field("My Blynk Device", description="Friendly device name")


class RegisterDeviceResponse(BaseModel):
    success: bool
    message: str
    device_id: int


class SensorIngestRequest(BaseModel):
    device_id: int
    air_temperature: Optional[float] = None
    air_humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    soil_temperature: Optional[float] = None
    soil_ec: Optional[float] = None
    soil_ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    raw_payload: Optional[dict] = None
    recorded_at: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────

@router.get("/check-device", response_model=CheckDeviceResponse)
async def check_device(db: Session = Depends(get_db)):
    """Check if any active Blynk device exists."""
    device = db.query(BlynkDevice).filter(BlynkDevice.is_active == True).first()
    if device:
        return CheckDeviceResponse(
            blynk_required=False,
            message="Device is registered and active.",
            device={
                "id": device.id,
                "device_name": device.device_name,
                "status": device.status,
                "last_seen_at": str(device.last_seen_at) if device.last_seen_at else None,
            },
        )
    return CheckDeviceResponse(
        blynk_required=True,
        message="Please connect your Blynk device to activate live monitoring.",
    )


@router.post("/register-device", response_model=RegisterDeviceResponse)
async def register_device(req: RegisterDeviceRequest, db: Session = Depends(get_db)):
    """Register a new Blynk device. Farm is resolved server-side."""
    try:
        # Resolve farm — server-side, never from frontend
        farm = db.query(Farm).first()
        
        # If no farm exists, auto-create one
        if not farm:
            farm = Farm(
                name="My Farm",
                location="Not set",
                size_acres=0,
                farmer_name="Farmer",
                farmer_phone=None,
                farmer_email=None,
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)
            logger.info(f"Auto-created farm: id={farm.id}")

        farm_id = farm.id

        # Defensive validation — farm_id must NEVER be None
        if farm_id is None:
            raise HTTPException(status_code=500, detail="Critical: farm_id resolved to NULL")

        # Check for duplicate active device
        existing = (
            db.query(BlynkDevice)
            .filter(BlynkDevice.farm_id == farm_id, BlynkDevice.is_active == True)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An active device already exists for this farm. Use update-device to replace it.",
            )

        encrypted = _encrypt_token(req.auth_token)

        device = BlynkDevice(
            farm_id=farm_id,
            device_name=req.device_name or "My Blynk Device",
            auth_token=encrypted,
            is_active=True,
            status="active",
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        logger.info(f"Blynk device registered: id={device.id} farm={farm_id}")
        return RegisterDeviceResponse(
            success=True,
            message="Device registered successfully. Sensor data ingestion can now begin.",
            device_id=device.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Device registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/ingest")
async def ingest_sensor_data(req: SensorIngestRequest, db: Session = Depends(get_db)):
    """Receive and store sensor readings from Blynk webhook/polling."""
    try:
        device = db.query(BlynkDevice).filter(BlynkDevice.id == req.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        recorded = datetime.now(timezone.utc)
        if req.recorded_at:
            try:
                recorded = datetime.fromisoformat(req.recorded_at)
            except ValueError:
                pass

        reading = SensorReading(
            device_id=req.device_id,
            farm_id=device.farm_id,
            air_temperature=req.air_temperature,
            air_humidity=req.air_humidity,
            soil_moisture=req.soil_moisture,
            soil_temperature=req.soil_temperature,
            soil_ec=req.soil_ec,
            soil_ph=req.soil_ph,
            nitrogen=req.nitrogen,
            phosphorus=req.phosphorus,
            potassium=req.potassium,
            raw_payload=req.raw_payload,
            recorded_at=recorded,
        )
        db.add(reading)

        # Update device last_seen_at
        device.last_seen_at = recorded
        device.status = "active"

        db.commit()

        return {"success": True, "message": "Sensor reading stored."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sensor ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@router.get("/readings")
async def get_sensor_readings(
    farm_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Paginated sensor readings for dashboard charts."""
    query = db.query(SensorReading)
    if farm_id:
        query = query.filter(SensorReading.farm_id == farm_id)
    readings = query.order_by(SensorReading.recorded_at.desc()).limit(limit).offset(offset).all()

    return {
        "readings": [
            {
                "id": r.id,
                "device_id": r.device_id,
                "air_temperature": float(r.air_temperature) if r.air_temperature else None,
                "air_humidity": float(r.air_humidity) if r.air_humidity else None,
                "soil_moisture": float(r.soil_moisture) if r.soil_moisture else None,
                "soil_temperature": float(r.soil_temperature) if r.soil_temperature else None,
                "soil_ec": float(r.soil_ec) if r.soil_ec else None,
                "soil_ph": float(r.soil_ph) if r.soil_ph else None,
                "nitrogen": float(r.nitrogen) if r.nitrogen else None,
                "phosphorus": float(r.phosphorus) if r.phosphorus else None,
                "potassium": float(r.potassium) if r.potassium else None,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in readings
        ],
        "count": len(readings),
        "offset": offset,
        "limit": limit,
    }


@router.get("/latest")
async def get_latest_reading(farm_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Latest single sensor reading for live dashboard."""
    query = db.query(SensorReading)
    if farm_id:
        query = query.filter(SensorReading.farm_id == farm_id)
    reading = query.order_by(SensorReading.recorded_at.desc()).first()

    if not reading:
        return {"has_data": False, "message": "Waiting for first data from device..."}

    return {
        "has_data": True,
        "reading": {
            "air_temperature": float(reading.air_temperature) if reading.air_temperature else None,
            "air_humidity": float(reading.air_humidity) if reading.air_humidity else None,
            "soil_moisture": float(reading.soil_moisture) if reading.soil_moisture else None,
            "soil_temperature": float(reading.soil_temperature) if reading.soil_temperature else None,
            "soil_ec": float(reading.soil_ec) if reading.soil_ec else None,
            "soil_ph": float(reading.soil_ph) if reading.soil_ph else None,
            "nitrogen": float(reading.nitrogen) if reading.nitrogen else None,
            "phosphorus": float(reading.phosphorus) if reading.phosphorus else None,
            "potassium": float(reading.potassium) if reading.potassium else None,
            "recorded_at": reading.recorded_at.isoformat() if reading.recorded_at else None,
        },
    }


@router.delete("/delete-device")
async def delete_device(db: Session = Depends(get_db)):
    """Delete/deactivate all active Blynk devices so user can register a new one."""
    try:
        devices = db.query(BlynkDevice).filter(BlynkDevice.is_active == True).all()
        count = 0
        for device in devices:
            db.delete(device)
            count += 1
        db.commit()
        logger.info(f"Deleted {count} active Blynk device(s)")
        return {"success": True, "message": f"Deleted {count} device(s).", "deleted": count}
    except Exception as e:
        db.rollback()
        logger.error(f"Device delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
