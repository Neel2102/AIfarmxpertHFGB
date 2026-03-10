"""
Voice API Routes
Handles speech-to-text (STT) and text-to-speech (TTS) with safe defaults.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import uuid
import io
from datetime import datetime

from farmxpert.services.voice.stt_service import STTService, StubSTTService
from farmxpert.services.voice.tts_service import TTSService, StubTTSService
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/voice", tags=["Voice"])
logger = get_logger("voice_api")


class STTRequest(BaseModel):
    language: Optional[str] = Field("en", description="Source language (auto-detected if not provided)")


class STTResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    language_detected: Optional[str] = None
    error: Optional[str] = None
    provider: str
    timestamp: str


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    language: Optional[str] = Field("en", description="Target language")
    voice_gender: Optional[str] = Field("neutral", description="Voice gender (male/female/neutral)")


class TTSResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    language_used: Optional[str] = None
    error: Optional[str] = None
    provider: str
    timestamp: str


def _safe_audio_bytes(file: UploadFile) -> Optional[bytes]:
    try:
        return file.file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded audio: {e}")
        return None


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file for speech-to-text"),
    language: Optional[str] = Form(None),
):
    """
    Upload audio and receive a transcript.
    Supports multipart/form-data; works with Swagger/Postman.
    """
    try:
        audio_bytes = _safe_audio_bytes(file)
        if audio_bytes is None:
            raise HTTPException(status_code=400, detail="Could not read uploaded audio")

        provider = STTService.get_default()
        result = await provider.transcribe_bytes(audio_bytes, source_language=language)

        response = STTResponse(
            success=result.get("success", False),
            transcript=result.get("transcript") if result.get("success") else None,
            language_detected=result.get("language_detected"),
            error=result.get("error") if not result.get("success") else None,
            provider=result.get("provider", "unknown"),
            timestamp=datetime.utcnow().isoformat(),
        )
        logger.info(f"STT completed: {response.provider} success={response.success}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in speech_to_text: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
):
    """
    Synthesize speech from text.
    Returns a temporary audio URL or a base64 blob if hosted storage is unavailable.
    """
    try:
        provider = TTSService.get_default()
        result = await provider.synthesize_speech(
            text=request.text,
            language=request.language or "en",
            voice_gender=request.voice_gender or "neutral",
        )

        response = TTSResponse(
            success=result.get("success", False),
            audio_url=result.get("audio_url") if result.get("success") else None,
            language_used=result.get("language_used") or request.language,
            error=result.get("error") if not result.get("success") else None,
            provider=result.get("provider", "unknown"),
            timestamp=datetime.utcnow().isoformat(),
        )
        logger.info(f"TTS completed: {response.provider} success={response.success}")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in text_to_speech: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/providers")
async def list_voice_providers():
    """List available STT/TTS providers (for UI dropdowns)."""
    return {
        "stt": {
            "default": STTService.get_default().name,
            "available": ["stub", "whisper", "azure", "google"],
            "current": STTService.get_default().name,
        },
        "tts": {
            "default": TTSService.get_default().name,
            "available": ["stub", "azure", "google", "coqui"],
            "current": TTSService.get_default().name,
        },
    }


@router.get("/status")
async def voice_status():
    """Health check for voice services."""
    return {
        "stt": {
            "provider": STTService.get_default().name,
            "ready": STTService.get_default().is_ready(),
        },
        "tts": {
            "provider": TTSService.get_default().name,
            "ready": TTSService.get_default().is_ready(),
        },
    }
