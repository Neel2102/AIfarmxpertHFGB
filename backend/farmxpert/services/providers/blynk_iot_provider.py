from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from farmxpert.config.settings import settings
from farmxpert.services.redis_cache_service import redis_cache


@dataclass(frozen=True)
class BlynkIoTCachePolicy:
    ttl_seconds: int = 5


class BlynkIoTProvider:
    def __init__(self, *, client: Optional[httpx.AsyncClient] = None, policy: BlynkIoTCachePolicy | None = None):
        self._client = client
        self._policy = policy or BlynkIoTCachePolicy()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _base_url(self) -> str:
        return (settings.blynk_base_url or "https://blr1.blynk.cloud/external/api/get").rstrip("/")

    def _token(self) -> Optional[str]:
        return settings.blynk_token

    def _cache_key(self) -> str:
        return "provider:iot:blynk:latest".lower()

    def _pins(self) -> Dict[str, str]:
        return {
            "air_temperature_c": "V0",
            "air_humidity_pct": "V1",
            "moisture_pct": "V2",
            "soil_temperature_c": "V3",
            "ec_us_cm": "V4",
            "ph": "V5",
            "nitrogen": "V6",
            "phosphorus": "V7",
            "potassium": "V8",
        }

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None

    async def get_latest(self) -> Dict[str, Any]:
        token = self._token()
        if not token:
            return {"success": False, "error": "BLYNK_TOKEN not configured", "fetched_at": self._now_iso()}

        cache_key = self._cache_key()
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        base_url = self._base_url()
        pins = self._pins()

        async with (self._client or httpx.AsyncClient(timeout=10)) as client:
            async def fetch_pin(pin: str) -> Optional[str]:
                r = await client.get(base_url, params={"token": token, pin: ""})
                r.raise_for_status()
                return (r.text or "").strip()

            values: Dict[str, Any] = {}
            errors: Dict[str, str] = {}
            for key, pin in pins.items():
                try:
                    values[key] = await fetch_pin(pin)
                except Exception as e:
                    errors[key] = str(e)
                    values[key] = None

        result = {
            "success": True,
            "source": "Blynk",
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
            "raw": values,
            "errors": errors or None,
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.ttl_seconds)
        return result

    async def get_soil_sensor_payload(self) -> Dict[str, Any]:
        latest = await self.get_latest()
        if not latest.get("success"):
            return latest

        raw = latest.get("raw") or {}

        ph = self._to_float(raw.get("ph"))
        n = self._to_float(raw.get("nitrogen"))
        p = self._to_float(raw.get("phosphorus"))
        k = self._to_float(raw.get("potassium"))
        ec_us_cm = self._to_float(raw.get("ec_us_cm"))
        moisture = self._to_float(raw.get("moisture_pct"))
        soil_temp = self._to_float(raw.get("soil_temperature_c"))

        ec_ds_m: Optional[float] = None
        if ec_us_cm is not None:
            ec_ds_m = ec_us_cm / 1000.0

        return {
            "success": True,
            "source": latest.get("source"),
            "fetched_at": latest.get("fetched_at"),
            "soil_data": {
                "pH": ph,
                "nitrogen": n,
                "phosphorus": p,
                "potassium": k,
                "electrical_conductivity": ec_ds_m,
                "moisture": moisture,
                "temperature": soil_temp,
            },
            "raw": raw,
            "errors": latest.get("errors"),
        }


blynk_iot_provider = BlynkIoTProvider()
