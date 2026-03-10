from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from farmxpert.core.utils.logger import get_logger
from farmxpert.models.blynk_models import BlynkDevice, SensorReading
from farmxpert.models.database import get_db
from farmxpert.models.farm_models import Farm

router = APIRouter(prefix="/iot", tags=["IoT"])
logger = get_logger("iot_api")


class SensorData(BaseModel):
    airTemperature: float
    airHumidity: float
    soilMoisture: float
    soilTemperature: float
    soilEC: float
    soilPH: float
    nitrogen: float
    phosphorus: float
    potassium: float


class IoTDataPayload(BaseModel):
    user_id: int
    source: str
    timestamp: str
    sensor_data: SensorData


def _parse_timestamp(ts: str) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)

    # Handle common ISO format from frontend, including trailing 'Z'
    normalized = ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@router.post("/inject")
async def inject_iot_data(payload: IoTDataPayload, db: Session = Depends(get_db)):
    try:
        farm = db.query(Farm).filter(Farm.user_id == payload.user_id).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found for user")

        device = (
            db.query(BlynkDevice)
            .filter(BlynkDevice.farm_id == farm.id, BlynkDevice.is_active == True)
            .first()
        )
        device_id = int(device.id) if device else 0

        recorded_at = _parse_timestamp(payload.timestamp)

        reading = SensorReading(
            device_id=device_id,
            farm_id=farm.id,
            air_temperature=payload.sensor_data.airTemperature,
            air_humidity=payload.sensor_data.airHumidity,
            soil_moisture=payload.sensor_data.soilMoisture,
            soil_temperature=payload.sensor_data.soilTemperature,
            soil_ec=payload.sensor_data.soilEC,
            soil_ph=payload.sensor_data.soilPH,
            nitrogen=payload.sensor_data.nitrogen,
            phosphorus=payload.sensor_data.phosphorus,
            potassium=payload.sensor_data.potassium,
            raw_payload={
                "source": payload.source,
                "timestamp": payload.timestamp,
                "user_id": payload.user_id,
            },
            recorded_at=recorded_at,
        )

        db.add(reading)
        db.commit()

        return {"status": "success", "message": "Sensor data injected"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"IoT inject failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to store sensor data")
