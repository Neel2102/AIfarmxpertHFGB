from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from farmxpert.config.settings import settings
from farmxpert.services.redis_cache_service import redis_cache


@dataclass(frozen=True)
class SchemesCachePolicy:
    ttl_seconds: int = 24 * 60 * 60
    stale_grace_seconds: int = 7 * 24 * 60 * 60


class SchemesProvider:

    def __init__(self, *, client: Optional[httpx.AsyncClient] = None, policy: SchemesCachePolicy | None = None):
        self._client = client
        self._policy = policy or SchemesCachePolicy()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _cache_key(self, query: str, region: Optional[str]) -> str:
        q = (query or "").strip().lower()
        r = (region or "").strip().lower()
        return f"provider:schemes:{q}:{r}".lower()

    def _is_authorized_url(self, url: str) -> bool:
        if not url:
            return False
        u = url.lower()
        return u.endswith(".gov.in") or ".gov.in/" in u or u.endswith(".nic.in") or ".nic.in/" in u or "india.gov.in" in u

    def _curated_schemes(self) -> List[Dict[str, Any]]:

        return [
            {
                "scheme_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Crop insurance to support farmers in case of crop loss due to natural calamities, pests, or diseases.",
                "state": "All",
                "official_url": "https://pmfby.gov.in",
                "source": "curated",
            },
            {
                "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Income support scheme providing annual financial assistance to eligible farmer families.",
                "state": "All",
                "official_url": "https://pmkisan.gov.in",
                "source": "curated",
            },
            {
                "scheme_name": "Soil Health Card Scheme",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Provides soil health cards with nutrient status and fertilizer recommendations.",
                "state": "All",
                "official_url": "https://soilhealth.dac.gov.in",
                "source": "curated",
            },
            {
                "scheme_name": "Kisan Credit Card (KCC)",
                "ministry": "Ministry of Finance / Banks",
                "description": "Credit facility for farmers to meet cultivation and post-harvest expenses.",
                "state": "All",
                "official_url": "https://kisan.gov.in",
                "source": "curated",
            },
        ]

    def _extract_ddg_results(self, html: str, *, max_results: int) -> List[Dict[str, Any]]:
        # DuckDuckGo HTML is not a stable API; this is best-effort parsing.
        # We deliberately keep this lightweight to avoid extra dependencies.
        import re

        results: List[Dict[str, Any]] = []
        if not html:
            return results

        # Matches: <a rel="nofollow" class="result__a" href="...">Title</a>
        pattern = re.compile(r"<a[^>]+class=\"result__a\"[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.IGNORECASE)
        for m in pattern.finditer(html):
            link = m.group(1)
            title = re.sub(r"<.*?>", "", m.group(2) or "").strip()
            if not self._is_authorized_url(link):
                continue
            if not title:
                continue
            results.append(
                {
                    "scheme_name": title,
                    "ministry": "",
                    "description": "",
                    "state": "All",
                    "official_url": link,
                    "source": "duckduckgo",
                }
            )
            if len(results) >= max_results:
                break

        return results

    async def _search_duckduckgo(self, query: str, *, max_results: int) -> List[Dict[str, Any]]:
        # Use the html endpoint (no key). Respect that this may be rate-limited.
        q = f"{query} site:.gov.in OR site:.nic.in OR site:india.gov.in"
        url = "https://duckduckgo.com/html/"
        params = {"q": q}
        headers = {"user-agent": "Mozilla/5.0"}

        async with (self._client or httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers)) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return self._extract_ddg_results(r.text, max_results=max_results)

    async def search_schemes(self, query: str, *, region: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:

        query_norm = (query or "").strip()
        if not query_norm:
            return {"success": False, "error": "query is required", "fetched_at": self._now_iso()}

        cache_key = self._cache_key(query_norm, region)
        cached = await redis_cache.get_json(cache_key)
        if cached:
            cached["cache"] = {"hit": True, "is_stale": False}
            return cached

        serp_key = settings.serpapi_api_key
        if not serp_key:
            schemes: List[Dict[str, Any]] = []
            try:
                schemes = await self._search_duckduckgo(query_norm if not region else f"{query_norm} {region}", max_results=max_results)
            except Exception:
                schemes = []

            if not schemes:
                schemes = self._curated_schemes()
                source = "curated"
            else:
                source = "DuckDuckGo"

            result = {
                "success": True,
                "source": source,
                "fetched_at": self._now_iso(),
                "cache": {"hit": False, "is_stale": False},
                "query": {"q": query_norm, "region": region, "max_results": max_results},
                "schemes": schemes,
            }
            await redis_cache.set_json(cache_key, result, ttl=self._policy.ttl_seconds)
            return result

        # SerpAPI Google search limited to government domains
        # Note: SerpAPI returns 'organic_results' with 'link' and 'snippet'.
        search_q = f"{query_norm} site:.gov.in OR site:.nic.in OR site:india.gov.in"
        params = {
            "api_key": serp_key,
            "engine": "google",
            "q": search_q,
            "num": min(int(max_results), 20),
            "gl": "in",
            "hl": "en",
        }

        schemes: List[Dict[str, Any]] = []
        try:
            async with (self._client or httpx.AsyncClient(timeout=20)) as client:
                r = await client.get("https://serpapi.com/search.json", params=params)
                r.raise_for_status()
                payload = r.json() or {}

            organic = payload.get("organic_results") or []
            for res in organic:
                link = (res.get("link") or "").strip()
                if not self._is_authorized_url(link):
                    continue
                title = (res.get("title") or "").strip()
                snippet = (res.get("snippet") or "").strip()
                if not title or not link:
                    continue
                schemes.append(
                    {
                        "scheme_name": title,
                        "ministry": "",
                        "description": snippet,
                        "state": "All",
                        "official_url": link,
                        "source": "serpapi",
                    }
                )
                if len(schemes) >= max_results:
                    break
        except Exception:
            schemes = []

        if not schemes:
            schemes = self._curated_schemes()
            source = "curated"
        else:
            source = "SerpAPI"

        result = {
            "success": True,
            "source": source,
            "fetched_at": self._now_iso(),
            "cache": {"hit": False, "is_stale": False},
            "query": {"q": query_norm, "region": region, "max_results": max_results},
            "schemes": schemes,
        }

        await redis_cache.set_json(cache_key, result, ttl=self._policy.ttl_seconds)
        return result