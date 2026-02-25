from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from farmxpert.config.settings import settings
from farmxpert.services.redis_cache_service import redis_cache


@dataclass(frozen=True)
class WeatherCachePolicy:
    current_ttl_seconds: int = 10 * 60
    forecast_ttl_seconds: int = 30 * 60
    geocode_ttl_seconds: int = 7 * 24 * 60 * 60
    stale_grace_seconds: int = 24 * 60 * 60


class WeatherProvider:
    """Production weather provider with caching.

    Uses OpenWeather endpoints:
    - Geocoding: /geo/1.0/direct
    - Current: /data/2.5/weather
    - Forecast: /data/2.5/forecast (3-hourly; aggregated to daily)
    """

    def __init__(self, *, client: Optional[httpx.AsyncClient] = None, policy: WeatherCachePolicy | None = None):
        self._client = client
        self._policy = policy or WeatherCachePolicy()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _cache_key(self, kind: str, identifier: str) -> str:
        return f"provider:weather:{kind}:{identifier}".lower()

    async def geocode(self, location: str) -> Dict[str, Any]:
        api_key = settings.openweather_api_key
        if not api_key:
            return {"success": False, "error": "OPENWEATHER_API_KEY not configured"}

        location_norm = (location or "").strip()
        if not location_norm:
            return {"success": False, "error": "location is required"}

        cache_key = self._cache_key("geocode", location_norm)
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {"q": location_norm, "limit": 1, "appid": api_key}

        async with (self._client or httpx.AsyncClient(timeout=15)) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json() or []

        if not data:
            result = {"success": False, "error": "location not found", "location": location_norm}
            await redis_cache.set_json(cache_key, result, ttl=self._policy.geocode_ttl_seconds)
            return result

        top = data[0]
        result = {
            "success": True,
            "location": location_norm,
            "geo": {
                "name": top.get("name"),
                "lat": top.get("lat"),
                "lon": top.get("lon"),
                "country": top.get("country"),
                "state": top.get("state"),
            },
            "source": "OpenWeather Geocoding",
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.geocode_ttl_seconds)
        return result

    async def get_current_by_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        api_key = settings.openweather_api_key
        if not api_key:
            return {"success": False, "error": "OPENWEATHER_API_KEY not configured"}

        cache_key = self._cache_key("current", f"{lat:.4f},{lon:.4f}")
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

        try:
            async with (self._client or httpx.AsyncClient(timeout=15)) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json() or {}
        except Exception as e:
            stale = await self._get_stale(cache_key)
            if stale:
                stale["cache"] = {"hit": True, "is_stale": True}
                stale["error"] = f"upstream_failed: {e}"
                return stale
            return {"success": False, "error": f"weather_current_failed: {e}"}

        result = {
            "success": True,
            "source": "OpenWeather Current",
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
            "data": {
                "coord": {"lat": lat, "lon": lon},
                "temperature_c": data.get("main", {}).get("temp"),
                "temp_min_c": data.get("main", {}).get("temp_min"),
                "temp_max_c": data.get("main", {}).get("temp_max"),
                "humidity_pct": data.get("main", {}).get("humidity"),
                "wind_speed_ms": data.get("wind", {}).get("speed"),
                "rain_1h_mm": (data.get("rain", {}) or {}).get("1h", 0.0),
                "clouds_pct": data.get("clouds", {}).get("all"),
                "condition": ((data.get("weather") or [{}])[0] or {}).get("main"),
                "condition_detail": ((data.get("weather") or [{}])[0] or {}).get("description"),
            },
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.current_ttl_seconds)
        return result

    async def get_forecast_by_coords(self, lat: float, lon: float, *, days: int = 7) -> Dict[str, Any]:
        api_key = settings.openweather_api_key
        if not api_key:
            return {"success": False, "error": "OPENWEATHER_API_KEY not configured"}

        days = max(1, min(int(days or 7), 7))
        cache_key = self._cache_key("forecast", f"{lat:.4f},{lon:.4f}:{days}d")
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

        try:
            async with (self._client or httpx.AsyncClient(timeout=20)) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json() or {}
        except Exception as e:
            stale = await self._get_stale(cache_key)
            if stale:
                stale["cache"] = {"hit": True, "is_stale": True}
                stale["error"] = f"upstream_failed: {e}"
                return stale
            return {"success": False, "error": f"weather_forecast_failed: {e}"}

        aggregated = self._aggregate_forecast_to_daily(data, days=days)
        alerts = self._derive_agri_alerts(aggregated)
        result = {
            "success": True,
            "source": "OpenWeather Forecast",
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
            "data": {
                "coord": {"lat": lat, "lon": lon},
                "days": days,
                "daily": aggregated,
                "alerts": alerts,
            },
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.forecast_ttl_seconds)
        return result

    async def get_weather_bundle(self, location: str, *, days: int = 7) -> Dict[str, Any]:
        geo = await self.geocode(location)
        if not geo.get("success"):
            return geo

        lat = geo["geo"]["lat"]
        lon = geo["geo"]["lon"]

        current = await self.get_current_by_coords(lat, lon)
        forecast = await self.get_forecast_by_coords(lat, lon, days=days)

        return {
            "success": True,
            "location": geo.get("location"),
            "geo": geo.get("geo"),
            "current": current,
            "forecast": forecast,
            "fetched_at": self._now_iso(),
            "sources": [
                current.get("source"),
                forecast.get("source"),
                geo.get("source"),
            ],
        }

    async def _get_stale(self, cache_key: str) -> Optional[Dict[str, Any]]:
        cached = await redis_cache.get_json(cache_key)
        if not cached:
            return None
        fetched_at = cached.get("fetched_at")
        if not fetched_at:
            return None
        return cached

    def _aggregate_forecast_to_daily(self, forecast_payload: Dict[str, Any], *, days: int) -> list[Dict[str, Any]]:
        items = forecast_payload.get("list") or []
        buckets: Dict[str, Dict[str, Any]] = {}

        for it in items:
            dt_txt = it.get("dt_txt")
            if not dt_txt or " " not in dt_txt:
                continue
            date_key = dt_txt.split(" ")[0]
            main = it.get("main") or {}
            rain_mm = ((it.get("rain") or {}) or {}).get("3h", 0.0) or 0.0
            pop = it.get("pop")
            temp = main.get("temp")
            tmin = main.get("temp_min")
            tmax = main.get("temp_max")
            hum = main.get("humidity")

            if date_key not in buckets:
                buckets[date_key] = {
                    "date": date_key,
                    "temp_min_c": tmin if tmin is not None else temp,
                    "temp_max_c": tmax if tmax is not None else temp,
                    "avg_humidity_pct": hum,
                    "rain_total_mm": float(rain_mm),
                    "pop_max": pop,
                    "conditions": set(),
                    "_count": 1,
                    "_humidity_sum": float(hum) if hum is not None else 0.0,
                }
            else:
                b = buckets[date_key]
                b["_count"] += 1
                if tmin is not None:
                    b["temp_min_c"] = min(b["temp_min_c"], tmin)
                if tmax is not None:
                    b["temp_max_c"] = max(b["temp_max_c"], tmax)
                b["rain_total_mm"] += float(rain_mm)
                if pop is not None:
                    b["pop_max"] = max(b.get("pop_max") or 0.0, pop)
                if hum is not None:
                    b["_humidity_sum"] += float(hum)

            cond = ((it.get("weather") or [{}])[0] or {}).get("main")
            if cond:
                buckets[date_key]["conditions"].add(str(cond))

        daily = []
        for date_key in sorted(buckets.keys())[:days]:
            b = buckets[date_key]
            count = max(1, int(b.pop("_count", 1)))
            hum_sum = float(b.pop("_humidity_sum", 0.0))
            avg_hum = hum_sum / count if hum_sum else None
            conditions = sorted(list(b.pop("conditions", set())))
            daily.append({
                **b,
                "avg_humidity_pct": avg_hum,
                "conditions": conditions,
            })

        return daily

    def _derive_agri_alerts(self, daily: list[Dict[str, Any]]) -> Dict[str, Any]:
        heat_threshold_c = 38.0
        dry_spell_days = 5
        dry_rain_threshold_mm = 2.0

        heat_days = [d for d in daily if (d.get("temp_max_c") is not None and float(d["temp_max_c"]) >= heat_threshold_c)]
        dry_spell = False
        if len(daily) >= dry_spell_days:
            window = daily[:dry_spell_days]
            rain = sum(float(d.get("rain_total_mm") or 0.0) for d in window)
            dry_spell = rain < dry_rain_threshold_mm

        return {
            "heat_stress": {
                "active": len(heat_days) > 0,
                "days": [d.get("date") for d in heat_days],
                "threshold_c": heat_threshold_c,
                "advice": "Avoid spraying in afternoon; irrigate early morning/evening; provide shade where possible." if heat_days else None,
            },
            "dry_spell": {
                "active": dry_spell,
                "window_days": dry_spell_days,
                "advice": "Dry spell likely; prioritize critical irrigation and mulching; delay sowing if not yet started." if dry_spell else None,
            },
        }