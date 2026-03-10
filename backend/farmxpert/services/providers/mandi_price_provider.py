from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from farmxpert.config.settings import settings
from farmxpert.services.redis_cache_service import redis_cache


@dataclass(frozen=True)
class MandiCachePolicy:
    prices_ttl_seconds: int = 30 * 60
    stale_grace_seconds: int = 24 * 60 * 60


class MandiPriceProvider:
    """Production mandi price provider (data.gov.in) with caching.

    This implementation expects:
    - DATA_GOV_API_KEY
    - DATA_GOV_RESOURCE_ID (Agmarknet/mandi price dataset resource id)
    """

    def __init__(self, *, client: Optional[httpx.AsyncClient] = None, policy: MandiCachePolicy | None = None):
        self._client = client
        self._policy = policy or MandiCachePolicy()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _cache_key(self, crops: List[str], location: str, limit: int) -> str:
        crops_key = ",".join(sorted((c or "").strip().lower() for c in crops if c))
        loc_key = (location or "").strip().lower()
        return f"provider:mandi:prices:{crops_key}:{loc_key}:{limit}".lower()

    def _parse_location(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """Best-effort parse into (state, district).

        Accepts:
        - "District, State"
        - "Village, District, State"
        - "State"
        """

        if not location:
            return None, None

        parts = [p.strip() for p in location.split(",") if p.strip()]
        if not parts:
            return None, None
        if len(parts) == 1:
            return parts[0], None
        if len(parts) == 2:
            return parts[1], parts[0]
        return parts[-1], parts[-2]

    async def get_mandi_prices(self, crops: List[str], location: str, *, limit_per_crop: int = 10) -> Dict[str, Any]:
        api_key = settings.data_gov_api_key
        resource_id = settings.data_gov_resource_id

        if not api_key or not resource_id:
            return {
                "success": False,
                "error": "DATA_GOV_API_KEY and DATA_GOV_RESOURCE_ID must be configured",
                "source": "data.gov.in",
                "fetched_at": self._now_iso(),
            }

        crops = [c for c in (crops or []) if (c or "").strip()]
        if not crops:
            return {"success": False, "error": "crops is required", "fetched_at": self._now_iso()}

        state, district = self._parse_location(location)
        cache_key = self._cache_key(crops, location, limit_per_crop)
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        mandi_prices: Dict[str, List[Dict[str, Any]]] = {}
        latest_snapshot: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        for crop in crops:
            try:
                rows = await self._fetch_crop_prices(
                    api_key=api_key,
                    resource_id=resource_id,
                    crop=crop,
                    state=state,
                    district=district,
                    limit=limit_per_crop,
                )
                normalized = [self._normalize_row(r) for r in rows]
                mandi_prices[crop] = normalized
                if normalized:
                    latest_snapshot[crop] = {
                        "mandi": normalized[0].get("mandi"),
                        "price": normalized[0].get("price"),
                        "date": normalized[0].get("date"),
                        "unit": normalized[0].get("unit"),
                    }
            except Exception as e:
                errors[crop] = str(e)
                mandi_prices[crop] = []

        result = {
            "success": True,
            "source": "data.gov.in",
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
            "query": {
                "location": location,
                "state": state,
                "district": district,
                "crops": crops,
                "limit_per_crop": limit_per_crop,
            },
            "mandi_prices": mandi_prices,
            "latest_snapshot": latest_snapshot,
            "data_sources": ["data.gov.in"],
            "errors": errors or None,
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.prices_ttl_seconds)
        return result

    async def _fetch_crop_prices(
        self,
        *,
        api_key: str,
        resource_id: str,
        crop: str,
        state: Optional[str],
        district: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        # data.gov.in "resource" API
        url = f"https://api.data.gov.in/resource/{resource_id}"

        params: Dict[str, Any] = {
            "api-key": api_key,
            "format": "json",
            "limit": int(limit),
        }

        # Common agmarknet fields vary by resource. We use best-effort filters.
        # If your resource uses different field names, we can adjust quickly.
        params["filters[commodity]"] = crop
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district

        async with (self._client or httpx.AsyncClient(timeout=20)) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            payload = r.json() or {}

        records = payload.get("records")
        if isinstance(records, list):
            return records
        return []

    def _normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Try multiple possible keys; different datasets may have different casing.
        def first(*keys: str) -> Any:
            for k in keys:
                if k in row and row[k] not in (None, ""):
                    return row[k]
            return None

        date = first("arrival_date", "date", "reported_date")
        mandi = first("market", "mandi", "market_name")
        state = first("state")
        district = first("district")
        commodity = first("commodity", "crop")
        variety = first("variety")

        # Prices
        modal = first("modal_price", "modal", "price")
        min_p = first("min_price", "min")
        max_p = first("max_price", "max")

        unit = first("unit", "price_unit") or "INR/quintal"

        return {
            "date": date,
            "mandi": mandi,
            "state": state,
            "district": district,
            "crop": commodity,
            "variety": variety,
            "price": modal,
            "min_price": min_p,
            "max_price": max_p,
            "unit": unit,
            "raw": row,
        }