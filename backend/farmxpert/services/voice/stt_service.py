"""
Speech-to-Text Service Interface
Pluggable STT backends.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional


class STTResult:
    def __init__(
        self,
        success: bool,
        transcript: Optional[str] = None,
        language_detected: Optional[str] = None,
        error: Optional[str] = None,
        provider: str = "unknown",
    ):
        self.success = success
        self.transcript = transcript
        self.language_detected = language_detected
        self.error = error
        self.provider = provider


class STTService(ABC):
    """Pluggable speech-to-text provider."""

    name: str

    @abstractmethod
    async def transcribe_bytes(self, audio_bytes: bytes, *, source_language: Optional[str] = None) -> STTResult:
        """Transcribe audio bytes to text."""
        ...

    def is_ready(self) -> bool:
        """Return True if the provider is ready."""
        return True


class StubSTTService(STTService):
    """Safe default: no real transcription; returns a clear error message."""

    name = "stub"

    async def transcribe_bytes(self, audio_bytes: bytes, *, source_language: Optional[str] = None) -> STTResult:
        return STTResult(
            success=False,
            error="STT not configured. Please configure a speech-to-text provider.",
            provider="stub",
        )

    def is_ready(self) -> bool:
        return True


# Registry/factory
_default_service: Optional[STTService] = None


def set_default_service(service: STTService) -> None:
    global _default_service
    _default_service = service


def get_default_service() -> STTService:
    global _default_service
    if _default_service is None:
        _default_service = StubSTTService()
    return _default_service
