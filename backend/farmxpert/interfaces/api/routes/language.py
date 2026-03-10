"""
Language API Routes
Handles language detection and translation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import json
from datetime import datetime

from farmxpert.services.language.language_service import LanguageService, StubLanguageService
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/language", tags=["Language"])
logger = get_logger("language_api")


class DetectRequest(BaseModel):
    text: str = Field(..., description="Text to detect language for")


class DetectResponse(BaseModel):
    success: bool
    detected: Optional[str] = None
    error: Optional[str] = None
    provider: str
    timestamp: str


class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target: str = Field(..., description="Target language code (e.g., hi, bn, ta)")


class TranslateResponse(BaseModel):
    success: bool
    detected: Optional[str] = None
    translated: Optional[str] = None
    target: Optional[str] = None
    error: Optional[str] = None
    provider: str
    timestamp: str


@router.post("/detect", response_model=DetectResponse)
async def detect_language(request: DetectRequest):
    """Detect language of given text (stub implementation)."""
    try:
        service = LanguageService.get_default_service()
        result = await service.detect(request.text)

        response = DetectResponse(
            success=result.success,
            detected=result.detected,
            error=result.error,
            provider=result.provider,
            timestamp=datetime.utcnow().isoformat(),
        )
        logger.info(f"Language detect: {response.provider} -> {response.detected}")
        return response
    except Exception as e:
        logger.error(f"Language detect failed: {e}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text to target language (stub implementation)."""
    try:
        service = LanguageService.get_default_service()
        result = await service.translate(request.text, request.target)

        response = TranslateResponse(
            success=result.success,
            detected=result.detected,
            translated=result.translated,
            target=result.target,
            error=result.error,
            provider=result.provider,
            timestamp=datetime.utcnow().isoformat(),
        )
        logger.info(f"Translate: {request.target} via {response.provider}")
        return response
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/providers")
async def list_language_providers():
    """List available language providers (for UI dropdowns)."""
    service = LanguageService.get_default_service()
    return {
        "default": service.name,
        "available": ["stub", "google_translate", "azure", "libretranslate"],
        "current": service.name,
    }
