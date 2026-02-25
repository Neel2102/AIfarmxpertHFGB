"""
Text-to-Speech Service Interface
Pluggable TTS backends.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional


class TTSResult:
    def __init__(
        self,
        success: bool,
        audio_url: Optional[str] = None,
        language_used: Optional[str] = None,
        error: Optional[str] = None,
        provider: str = "unknown",
    ):
        self.success = success
        self.audio_url = audio_url
        self.language_used = language_used
        self.error = error
        self.provider = provider


class TTSService(ABC):
    """Pluggable text-to-speech provider."""

    name: str

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        *,
        language: str = "en",
        voice_gender: str = "neutral",
    ) -> TTSResult:
        """Synthesize speech from text."""
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is ready."""
        return True


class StubTTSService(TTSService):
    """Safe default: no real synthesis; returns a clear error message."""

    name = "stub"

    async def synthesize_speech(
        self,
        text: str,
        *,
        language: str = "en",
        voice_gender: str = "neutral",
    ) -> TTSResult:
        return TTSResult(
            success=False,
            error="TTS not configured. Please configure a text-to-speech provider.",
            provider="stub",
        )

    def is_ready(self) -> bool:
        return True


# Registry/factory
_default_service: Optional[TTSService] = None


def set_default_service(service: TTSService) -> None:
    global _default_service
    _default_service = service


def get_default_service() -> TTSService:
    global _default_service
    if _default_service is None:
        _default_service = StubTTSService()
    return _default_service
