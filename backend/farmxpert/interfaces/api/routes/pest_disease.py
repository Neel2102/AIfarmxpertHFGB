"""
Pest & Disease Diagnostic API Routes
Handles image uploads and inference for pest/disease identification.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import uuid
import base64
import io
from datetime import datetime

from farmxpert.services.providers.pest_disease_inference import PestDiseaseInferenceProvider, StubInferenceProvider
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/pest-disease", tags=["Pest Disease"])
logger = get_logger("pest_disease_api")


class ImageDiagnosisRequest(BaseModel):
    crop: Optional[str] = Field(None, description="Crop name (e.g., wheat, rice)")
    location: Optional[str] = Field(None, description="Location (e.g., Pune, Maharashtra)")
    language: Optional[str] = Field("en", description="Language for response")


class ImageDiagnosisResponse(BaseModel):
    success: bool
    diagnosis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    image_metadata: Optional[Dict[str, Any]] = None
    provider: str
    timestamp: str


def _safe_image_bytes(file: UploadFile) -> Optional[bytes]:
    try:
        return file.file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded image: {e}")
        return None


def _make_thumbnail(image_bytes: bytes, size: tuple = (128, 128)) -> Optional[str]:
    """Return a small base64 thumbnail for UI previews (optional)."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        thumb_b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{thumb_b64}"
    except Exception:
        return None


@router.post("/diagnose-image", response_model=ImageDiagnosisResponse)
async def diagnose_image(
    file: UploadFile = File(..., description="Crop/plant image for diagnosis"),
    crop: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
):
    """
    Upload an image and receive pest/disease diagnosis.
    Supports multipart/form-data; works with Swagger/Postman.
    """
    try:
        image_bytes = _safe_image_bytes(file)
        if image_bytes is None:
            raise HTTPException(status_code=400, detail="Could not read uploaded image")

        # Basic metadata
        image_metadata = {
            "filename": file.filename,
            "size_bytes": len(image_bytes),
            "content_type": file.content_type,
            "thumbnail": _make_thumbnail(image_bytes),
        }

        # Inference (plugable provider)
        provider = PestDiseaseInferenceProvider.get_default()
        result = await provider.infer_from_bytes(image_bytes, crop=crop or "", location=location or "")

        # Normalize response for UI
        response = ImageDiagnosisResponse(
            success=result.get("success", False),
            diagnosis=result.get("diagnosis") if result.get("success") else None,
            error=result.get("error") if not result.get("success") else None,
            image_metadata=image_metadata,
            provider=result.get("provider", "unknown"),
            timestamp=datetime.utcnow().isoformat(),
        )

        logger.info(f"Diagnosis completed: {response.provider} success={response.success}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diagnose_image: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@router.get("/providers")
async def list_providers():
    """List available inference providers (for UI dropdowns)."""
    return {
        "default": PestDiseaseInferenceProvider.get_default().name,
        "available": ["stub", "local", "huggingface", "roboflow"],
        "current": PestDiseaseInferenceProvider.get_default().name,
    }


@router.get("/status")
async def inference_status():
    """Health check for inference backend."""
    provider = PestDiseaseInferenceProvider.get_default()
    return {
        "provider": provider.name,
        "ready": provider.is_ready(),
        "supports_image_upload": True,
        "supports_region": provider.supports_region(),
        "supports_multilingual": provider.supports_multilingual(),
    }
