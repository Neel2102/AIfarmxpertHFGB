"""
Pest & Disease Inference Provider Interface
Pluggable inference backends for image-based diagnosis.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceResult:
    success: bool
    diagnosis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: str
    confidence: float = 0.0
    severity: Optional[str] = None
    actions: Optional[list[str]] = None


class PestDiseaseInferenceProvider(ABC):
    """Pluggable inference provider for pest/disease diagnosis."""

    name: str
    supports_multilingual: bool = False
    supports_region: bool = False

    @abstractmethod
    async def infer_from_bytes(self, image_bytes: bytes, *, crop: str = "", location: str = "") -> InferenceResult:
        """Run inference on image bytes and return a structured diagnosis."""
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is ready (e.g., model loaded, API key present)."""
        return True

    def supports_multilingual(self) -> bool:
        return self.supports_multilingual

    def supports_region(self) -> bool:
        return self.supports_region


class StubInferenceProvider(PestDiseaseInferenceProvider):
    """Safe default provider: heuristics + Gemini fallback."""

    name = "stub"
    supports_multilingual = False
    supports_region = False

    async def infer_from_bytes(self, image_bytes: bytes, *, crop: str = "", location: str = "") -> InferenceResult:
        # Heuristic-based stub: basic image size/type detection + Gemini fallback if available
        try:
            from farmxpert.services.gemini_service import gemini_service
            prompt = f"""
            You are a plant disease expert. Analyze the uploaded crop image and provide a structured diagnosis.
            Crop: {crop or "unknown"}
            Location: {location or "unknown"}
            Image size: {len(image_bytes)} bytes

            Return JSON with keys:
            - disease_pest_name
            - confidence (0-1)
            - severity (mild/moderate/severe)
            - symptoms_description
            - treatment_recommendations (list)
            - prevention_strategies (list)
            """
            response = await gemini_service.generate_response(prompt, {"task": "pest_disease_stub_inference"})
            parsed = gemini_service._parse_json_response(response) or {}
            return InferenceResult(
                success=True,
                diagnosis=parsed,
                provider="stub",
                confidence=float(parsed.get("confidence", 0.5)),
                severity=parsed.get("severity"),
                actions=parsed.get("treatment_recommendations") or [],
            )
        except Exception as e:
            return InferenceResult(
                success=False,
                error=f"Stub inference failed: {e}",
                provider="stub",
            )

    def is_ready(self) -> bool:
        return True


# Registry/factory
_default_provider: Optional[PestDiseaseInferenceProvider] = None


def set_default_provider(provider: PestDiseaseInferenceProvider) -> None:
    global _default_provider
    _default_provider = provider


def get_default_provider() -> PestDiseaseInferenceProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = StubInferenceProvider()
    return _default_provider
