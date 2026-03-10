"""
Language Detection & Translation Service
Pluggable backends; safe defaults.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional


class LanguageResult:
    def __init__(
        self,
        success: bool,
        detected: Optional[str] = None,
        translated: Optional[str] = None,
        target: Optional[str] = None,
        error: Optional[str] = None,
        provider: str = "unknown",
    ):
        self.success = success
        self.detected = detected
        self.translated = translated
        self.target = target
        self.error = error
        self.provider = provider


class LanguageService(ABC):
    """Pluggable language detection/translation provider."""

    name: str

    @abstractmethod
    async def detect(self, text: str) -> LanguageResult:
        """Detect language of given text."""
        ...

    @abstractmethod
    async def translate(self, text: str, target: str) -> LanguageResult:
        """Translate text to target language."""
        ...


class StubLanguageService(LanguageService):
    """Safe default: passthrough + simple heuristics."""

    name = "stub"

    async def detect(self, text: str) -> LanguageResult:
        # Very basic heuristics (no external APIs)
        indicators = {
            "hi": ["namaste", "kya", "hai", "mein", "kaise", "hai"],
            "bn": ["কোষাট", "কোলাট", "কোভাট", "কোজান", "কোজান"],
            "ta": ["வணகள்", "என்ன", "எத்த", "எங்கள்", "என்ன"],
            "te": ["మీరో", "ఎలు", "ఎంది", "ఎండి", "ఎండి"],
            "mr": ["मी", "आहे", "आहे", "का", "की", "आहे", "आपले"],
            "gu": ["શુભ", "છે", "છે", "છે", "છે"],
            "pa": ["ਸਤ", "ਹਨ", "ਹਨ", "ਹਨ", "ਹਨ"],
            "or": ["ଓ", "ନା", "ନା", "ନା", "ନା"],
            "as": ["মোৰ", "কো", "কো", "কো", "কো"],
            "kn": ["ನಮಸ್ಪ", "ಏನೆ", "ಏಳೆ", "ಏಳೆ", "ಏಳೆ"],
            "ml": ["എന്നു", "എന്നു", "എന്നു", "എന്നു"],
        }

        detected = "en"
        for lang, tokens in indicators.items():
            if any(tok in text.lower() for tok in tokens):
                detected = lang
                break

        return LanguageResult(
            success=True,
            detected=detected,
            provider="stub",
        )

    async def translate(self, text: str, target: str) -> LanguageResult:
        # Passthrough: no real translation
        return LanguageResult(
            success=True,
            detected="en",
            translated=text,
            target=target,
            provider="stub",
        )


# Registry/factory
_default_service: Optional[LanguageService] = None


def set_default_service(service: LanguageService) -> None:
    global _default_service
    _default_service = service


def get_default_service() -> LanguageService:
    global _default_service
    if _default_service is None:
        _default_service = StubLanguageService()
    return _default_service
