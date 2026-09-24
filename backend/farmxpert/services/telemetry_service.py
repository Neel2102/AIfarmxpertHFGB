"""
Canonical telemetry service.

Before this existed there were two unrelated data paths:

  Hardware IoT page   -> browser -> https://blr1.blynk.cloud/external/api/get
                         (live values, but only while that page is open, and
                          with the farmer's Blynk auth token exposed in the
                          browser)

  Soil & Sensors page -> browser -> backend -> `sensor_readings` / `soil_tests`
                         (only ever populated as a side effect of the Hardware
                          page being open, so normally empty)

That is why Hardware IoT showed live readings while Soil & Sensors showed "--".

This module makes the backend the single source of truth: it reads Blynk with
the token already stored against the farmer's registered device, normalises the
result, persists it, and serves it to every page through one endpoint.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from urllib.parse import quote
from sqlalchemy.orm import Session

from farmxpert.models.blynk_models import BlynkDevice, SensorReading

logger = logging.getLogger(__name__)

DEFAULT_BLYNK_BASE_URL = "https://blr1.blynk.cloud"

# Virtual pin -> canonical field name. This is the wiring of the device that is
# actually deployed; it is the same mapping the Hardware IoT page uses.
PIN_MAP = {
    "V0": "air_temperature",
    "V1": "air_humidity",
    "V2": "soil_moisture",
    "V3": "soil_temperature",
    "V4": "soil_ec",
    "V5": "soil_ph",
    "V6": "nitrogen",
    "V7": "phosphorus",
    "V8": "potassium",
}

TELEMETRY_FIELDS = tuple(PIN_MAP.values())

# A live poll is reused for this long. The device pushes roughly every few
# seconds; polling Blynk once per dashboard render for every open tab would be
# both slow and rude to their API.
CACHE_TTL = timedelta(seconds=15)


def _parse_numeric(value: Any) -> Optional[float]:
    """
    Convert a Blynk pin value to a float.

    Returns None for anything unusable. Crucially it never returns 0 as a
    stand-in for "missing": 0 is a legitimate sensor reading, so conflating the
    two would show the farmer a real-looking measurement that does not exist.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "nan", "undefined"}:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def decrypt_token(stored: str) -> str:
    """Reverse of blynk_routes._encrypt_token (salt prefix + ':' + token)."""
    if stored and ":" in stored:
        return stored.split(":", 1)[1]
    return stored


def get_active_device(db: Session, user_id: int) -> Optional[BlynkDevice]:
    """
    The farmer's registered device.

    NOTE on BlynkDevice.farm_id: registration stores the authenticated *user id*
    in this column (the model documents it as a logical reference with no FK).
    Every read path uses the same convention, which is what keeps devices scoped
    to their owner. Do not "fix" this to a real farm id without migrating the
    existing rows.
    """
    return (
        db.query(BlynkDevice)
        .filter(BlynkDevice.farm_id == user_id, BlynkDevice.is_active == True)  # noqa: E712
        .first()
    )


async def fetch_from_blynk(auth_token: str, base_url: str = DEFAULT_BLYNK_BASE_URL) -> Dict[str, Optional[float]]:
    """
    Read all nine virtual pins from the Blynk cloud.

    Raises httpx.HTTPError if the device or token is unreachable, so the caller
    can report a genuine connection problem instead of showing stale or
    fabricated values.
    """
    readings: Dict[str, Optional[float]] = {field: None for field in TELEMETRY_FIELDS}
    url = base_url.rstrip("/") + "/external/api/get"

    async with httpx.AsyncClient(timeout=10.0) as client:
        for pin, field in PIN_MAP.items():
            try:
                # Blynk expects a bare pin flag: ?token=<t>&V2  (not "&V2=").
                # This is the exact form the Hardware IoT page used against the
                # Blynk cloud, so it is known to work with the deployed device.
                response = await client.get(
                    url + "?token=" + quote(auth_token, safe="") + "&" + pin
                )
                if response.status_code == 200:
                    readings[field] = _parse_numeric(response.text)
                elif response.status_code in (400, 401, 403):
                    # Blynk rejects the token itself — no point trying the rest.
                    raise httpx.HTTPStatusError(
                        "Blynk rejected the device token",
                        request=response.request,
                        response=response,
                    )
                else:
                    logger.warning("Blynk pin %s returned HTTP %s", pin, response.status_code)
            except httpx.HTTPStatusError:
                raise
            except httpx.HTTPError as e:
                # One unreadable pin should not discard the other eight.
                logger.warning("Blynk pin %s unreadable: %s", pin, e)

    return readings


def persist_reading(db: Session, device: BlynkDevice, values: Dict[str, Optional[float]]) -> Optional[SensorReading]:
    """
    Store a poll result so Soil & Sensors has history and the season planner has
    real soil data. A poll where every pin was unreadable is not stored — an
    all-NULL row is noise, not a measurement.
    """
    if not any(v is not None for v in values.values()):
        return None

    reading = SensorReading(
        device_id=device.id,
        farm_id=device.farm_id,
        recorded_at=datetime.now(timezone.utc),
        raw_payload={k: v for k, v in values.items() if v is not None},
        **{field: values.get(field) for field in TELEMETRY_FIELDS},
    )
    db.add(reading)
    device.last_seen_at = datetime.now(timezone.utc)
    device.status = "active"
    device.last_error = None
    db.commit()
    db.refresh(reading)
    return reading


def latest_stored_reading(db: Session, device: BlynkDevice) -> Optional[SensorReading]:
    return (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device.id)
        .order_by(SensorReading.recorded_at.desc())
        .first()
    )


def reading_to_payload(reading: SensorReading) -> Dict[str, Optional[float]]:
    """Normalise a stored row into the telemetry contract (None stays None)."""
    payload: Dict[str, Any] = {}
    for field in TELEMETRY_FIELDS:
        value = getattr(reading, field, None)
        payload[field] = float(value) if value is not None else None
    payload["recorded_at"] = reading.recorded_at.isoformat() if reading.recorded_at else None
    return payload


async def get_live_telemetry(db: Session, user_id: int, base_url: str = DEFAULT_BLYNK_BASE_URL) -> Dict[str, Any]:
    """
    The one telemetry read every page uses.

    Response contract:
      connected  — the farmer has a registered, active device
      has_data   — at least one real measurement is present
      status     — not_connected | waiting_for_data | active | stale
      source     — blynk (just polled) | database (last stored reading)
      data       — the nine fields, each a float or null. Never 0-as-missing.
    """
    device = get_active_device(db, user_id)
    if not device:
        return {
            "connected": False,
            "has_data": False,
            "status": "not_connected",
            "message": "Your IoT device is not connected yet.",
            "device": None,
            "data": None,
        }

    device_info = {
        "id": device.id,
        "device_name": device.device_name,
        "status": device.status,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
    }

    stored = latest_stored_reading(db, device)

    # Serve a very recent poll straight from the database.
    if stored and stored.recorded_at and datetime.now(timezone.utc) - stored.recorded_at < CACHE_TTL:
        return {
            "connected": True,
            "has_data": True,
            "status": "active",
            "source": "database",
            "device": device_info,
            "data": reading_to_payload(stored),
        }

    try:
        values = await fetch_from_blynk(decrypt_token(device.auth_token), base_url)
        reading = persist_reading(db, device, values)
        if reading:
            return {
                "connected": True,
                "has_data": True,
                "status": "active",
                "source": "blynk",
                "device": device_info,
                "data": reading_to_payload(reading),
            }
    except httpx.HTTPStatusError as e:
        device.status = "invalid_token"
        device.last_error = "Blynk rejected the device token"
        db.commit()
        logger.warning("Blynk auth failure for device %s: %s", device.id, e)
    except httpx.HTTPError as e:
        device.last_error = str(e)[:500]
        db.commit()
        logger.warning("Blynk unreachable for device %s: %s", device.id, e)

    # Live read failed. Fall back to the last real stored reading and label it
    # stale, so the farmer sees a genuine measurement with an honest timestamp
    # rather than a fabricated "current" value.
    if stored:
        return {
            "connected": True,
            "has_data": True,
            "status": "stale",
            "source": "database",
            "message": "Showing the most recent stored reading; the device is not responding right now.",
            "device": device_info,
            "data": reading_to_payload(stored),
        }

    return {
        "connected": True,
        "has_data": False,
        "status": "waiting_for_data",
        "message": "Device registered. Waiting for the first sensor reading.",
        "device": device_info,
        "data": None,
    }
