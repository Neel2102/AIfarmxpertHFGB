"""
FarmXpert Unified Chat API Routes
Provides the following endpoints:
  POST /api/chat/orchestrate  - Text chat routed to SuperAgent (real AI)
  POST /api/chat/vision       - Image upload → Pest & Disease Diagnostic Agent (Gemini vision)
  POST /api/chat/voice        - Audio upload → STT → SuperAgent → TTS → audio/mpeg response
  POST /api/chat/document     - PDF/CSV/TXT upload → Gemini document analysis
"""

import os
import io
import json
import base64
import logging
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from sqlalchemy.orm import Session
from farmxpert.models.database import get_db
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.farm_models import Farm, SoilTest
from farmxpert.app.shared.utils import logger
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.models.user_models import User

router = APIRouter(prefix="/chat", tags=["Chat"])

# ---------------------------------------------------------------------------
# Gemini initialisation
# ---------------------------------------------------------------------------

from farmxpert.config.settings import settings

def _get_gemini_model(model_name: str = "gemini-1.5-flash"):
    """Return a configured Gemini GenerativeModel."""
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


# ---------------------------------------------------------------------------
# Helper: call orchestrator and format response
# ---------------------------------------------------------------------------

async def _call_orchestrator(message: str, user_id: int, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call SuperAgent and return a clean response dict."""
    from farmxpert.core.super_agent import super_agent
    
    payload: Dict[str, Any] = {
        "query": message,
        "user_id": str(user_id),
        "context": extra or {}
    }

    result = await super_agent.process_query(
        query=message,
        context=payload,
        session_id=extra.get("session_id") if extra else None
    )

    # Extract the best human-readable text from the result
    response_text = result.natural_language or result.response.get("response", "") if result.success else str(result.response.get("answer", ""))

    # Build agent_responses list for the frontend chips
    agent_responses = []
    for agent_response in result.agent_responses:
        agent_responses.append({
            "agent_name": agent_response.agent_name,
            "success": agent_response.success,
            "summary": agent_response.data.get("response", "")[:100] + "..." if agent_response.success else agent_response.error,
        })

    return {
        "success": result.success,
        "response": response_text,
        "query_type": "super_agent",
        "agent_responses": agent_responses,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ===========================================================================
# PHASE 1 — POST /api/chat/orchestrate (Text Chat)
# ===========================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[int] = None # This field is now optional as current_user.id is used
    context: Optional[Dict[str, Any]] = None


@router.post("/orchestrate")
async def chat_orchestrate(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unified text chat endpoint (requires authentication).
    Routes the user message to the SuperAgent which selects the
    appropriate sub-agents and returns a synthesized response.
    The authenticated user_id is forwarded so chat history is user-scoped.
    """
    try:
        logger.info(f"[chat/orchestrate] user={current_user.id} message={request.message[:80]!r}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        extra = {}
        if request.context:
            extra.update(request.context)

        # ── Fetch User Farm Profile, Farm Layout Coordinates, and Live Sensors ──
        try:
            farm_profile = db.query(FarmProfile).filter(FarmProfile.user_id == current_user.id).first()
            farm = db.query(Farm).filter(Farm.user_id == current_user.id).first()

            # Coordinates resolution
            lat = None
            lon = None
            if farm_profile:
                lat = farm_profile.latitude
                lon = farm_profile.longitude
                if (not lat or not lon) and isinstance(farm_profile.farm_polygon, dict):
                    coords = farm_profile.farm_polygon.get("coordinates")
                    if coords and isinstance(coords, list) and len(coords) > 0:
                        first_ring = coords[0]
                        if isinstance(first_ring, list) and len(first_ring) > 0:
                            first_pt = first_ring[0]
                            if isinstance(first_pt, list) and len(first_pt) >= 2:
                                lon = float(first_pt[0])
                                lat = float(first_pt[1])
            if (not lat or not lon) and farm:
                lat = float(farm.latitude) if farm.latitude else None
                lon = float(farm.longitude) if farm.longitude else None

            # Location string resolution
            loc_str = None
            district = None
            state = None
            if farm_profile:
                loc_str = farm_profile.location or (f"{farm_profile.district}, {farm_profile.state}" if farm_profile.district and farm_profile.state else None)
                district = farm_profile.district
                state = farm_profile.state
            if not loc_str and farm:
                loc_str = f"{farm.district}, {farm.state}" if farm.district and farm.state else farm.state or farm.district
                district = farm.district
                state = farm.state
            if not loc_str and hasattr(current_user, "location") and current_user.location:
                loc_str = current_user.location

            # Crop list resolution
            crops = []
            if farm_profile and farm_profile.primary_crops:
                if isinstance(farm_profile.primary_crops, list):
                    crops.extend([str(c) for c in farm_profile.primary_crops])
                elif isinstance(farm_profile.primary_crops, str):
                    crops.extend([c.strip() for c in farm_profile.primary_crops.split(",") if c.strip()])
            if farm_profile and farm_profile.specific_crop and farm_profile.specific_crop not in crops:
                crops.append(farm_profile.specific_crop)
            if farm and farm.crop_type and farm.crop_type not in crops:
                crops.append(farm.crop_type)

            soil_type = farm_profile.soil_type if farm_profile and farm_profile.soil_type else (farm.soil_type if farm and farm.soil_type else None)

            # Latest soil sensor test
            soil_test = None
            if farm:
                soil_test = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.test_date.desc()).first()
            if not soil_test:
                soil_test = db.query(SoilTest).order_by(SoilTest.test_date.desc()).first()

            soil_telemetry = {}
            if soil_test:
                soil_telemetry = {
                    "moisture": soil_test.soil_moisture,
                    "temperature": soil_test.soil_temperature or soil_test.air_temperature,
                    "ph": soil_test.soil_ph,
                    "nitrogen": soil_test.nitrogen,
                    "phosphorus": soil_test.phosphorus,
                    "potassium": soil_test.potassium,
                    "ec": soil_test.soil_ec,
                    "humidity": soil_test.air_humidity,
                    "tested_at": soil_test.test_date.isoformat() if soil_test.test_date else None
                }

            # Enriched Context Attributes
            extra["farmer_name"] = current_user.full_name or current_user.username or "Farmer"
            if lat and lon:
                extra["latitude"] = lat
                extra["longitude"] = lon
                extra["location"] = {"latitude": lat, "longitude": lon, "name": loc_str or "Local Farm"}
            elif loc_str:
                extra["location"] = loc_str
            extra["location_text"] = loc_str or "India"
            extra["district"] = district
            extra["state"] = state
            extra["crops"] = crops
            extra["crop"] = crops[0] if crops else None
            extra["soil_type"] = soil_type
            extra["soil_data"] = soil_telemetry
            extra["soil_telemetry"] = soil_telemetry
            if farm_profile:
                extra["farm_size"] = f"{farm_profile.farm_size} {farm_profile.farm_size_unit or 'acres'}" if farm_profile.farm_size else None
                extra["water_source"] = farm_profile.water_source
                extra["irrigation_method"] = farm_profile.irrigation_method
                extra["season"] = farm_profile.cropping_season
        except Exception as err:
            logger.warning(f"Error enriching user farm context in chat_orchestrate: {err}")
            
        # Extract chat history so we can pass it to the AI for conversational memory
        try:
            from farmxpert.interfaces.api.routes.super_agent import _db_get_history
            chat_history = _db_get_history(session_id, user_id=current_user.id)
            # Pass the last 10 turns
            extra["chat_history"] = chat_history[-10:] if chat_history else []
        except Exception as e:
            logger.warning(f"Failed to fetch chat history context: {e}")
            extra["chat_history"] = []
                
        extra["session_id"] = session_id
                
        response = await _call_orchestrator(
            request.message,
            user_id=current_user.id,
            extra=extra or None,
        )
        
        # Save chat history
        try:
            from farmxpert.interfaces.api.routes.super_agent import _db_save_message
            _db_save_message(session_id, "user", request.message, user_id=current_user.id)
            _db_save_message(session_id, "assistant", response.get("response", ""), user_id=current_user.id)
        except Exception as e:
            logger.warning(f"Failed to save chat history: {e}")
            
        # Include session_id in the response so the frontend can track it
        response["session_id"] = session_id
        return response
    except Exception as e:
        logger.error(f"[chat/orchestrate] error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# ===========================================================================
# PHASE 2+3 — POST /api/chat/vision (Image → Pest Diagnostic)
# ===========================================================================

@router.post("/vision")
async def chat_vision(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(..., description="Crop / leaf image (JPEG, PNG, WebP)"),
    prompt: Optional[str] = Form(None, description="Optional additional context"),
    crop: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """
    Upload a crop image and receive a structured Pest & Disease diagnosis
    from the Gemini Vision model (requires authentication).
    """
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        content_type = file.content_type or "image/jpeg"
        logger.info(f"[chat/vision] user={current_user.id} file={file.filename!r}, size={len(image_bytes)}, content_type={content_type}")

        # Build vision prompt
        context_parts = []
        if crop:
            context_parts.append(f"Crop: {crop}")
        if location:
            context_parts.append(f"Location: {location}")
        if prompt:
            context_parts.append(f"Additional context: {prompt}")
        ctx_str = "\n".join(context_parts) if context_parts else ""

        vision_prompt = f"""You are an expert agricultural plant pathologist and pest diagnostician.
Analyze this crop/leaf image carefully and identify any pest infestation or disease.

{ctx_str}

Respond ONLY with a valid JSON object in this exact format (no markdown, no code fences):
{{
  "diagnosis": "<name of disease or pest, or 'Healthy' if no issue>",
  "confidence": <float 0.0-1.0>,
  "severity": "<none|mild|moderate|severe>",
  "description": "<2-3 sentence description of what you observe>",
  "recommended_treatment": ["<treatment 1>", "<treatment 2>", "<treatment 3>"],
  "prevention": ["<prevention tip 1>", "<prevention tip 2>"]
}}"""

        model = _get_gemini_model("gemini-1.5-flash")
        image_part = {"mime_type": content_type, "data": image_bytes}

        import asyncio
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, [vision_prompt, image_part]),
            timeout=30,
        )

        raw_text = ""
        try:
            raw_text = response.text
        except Exception:
            try:
                raw_text = response.candidates[0].content.parts[0].text
            except Exception:
                raw_text = str(response)

        # Parse the JSON from Gemini's response
        vision_result = _parse_json_safe(raw_text)

        # Ensure minimum required fields
        if not vision_result or "diagnosis" not in vision_result:
            vision_result = {
                "diagnosis": raw_text,
                "confidence": 0.5,
                "severity": "unknown",
                "description": raw_text,
                "recommended_treatment": ["Consult a local agronomist"],
                "prevention": [],
            }

        human_summary = (
            f"Diagnosis: **{vision_result.get('diagnosis', 'Unknown')}** "
            f"(confidence: {int(float(vision_result.get('confidence', 0)) * 100)}%). "
            f"{vision_result.get('description', '')} "
            f"Severity: {vision_result.get('severity', 'unknown')}."
        )

        if session_id:
            try:
                from farmxpert.interfaces.api.routes.super_agent import _db_save_message
                user_msg = f"[📷 Image: {file.filename}] {prompt or ''}".strip()
                _db_save_message(session_id, "user", user_msg, user_id=current_user.id)
                _db_save_message(session_id, "assistant", human_summary, user_id=current_user.id)
            except Exception as e:
                logger.warning(f"Failed to save vision chat history: {e}")

        return {
            "success": True,
            "vision_result": vision_result,
            "response": human_summary,
            "filename": file.filename,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[chat/vision] error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# ===========================================================================
# PHASE 4 — POST /api/chat/voice (Audio → STT → Orchestrator → TTS)
# ===========================================================================

@router.post("/voice")
async def chat_voice(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(..., description="Audio blob (webm, mp3, wav, ogg)"),
    language: Optional[str] = Form("en"),
    session_id: Optional[str] = Form(None),
):
    """
    Voice Super Agent loop (requires authentication):
    1. Transcribe audio via Gemini STT
    2. Route transcript to SuperAgent (scoped to this user)
    3. Convert response to speech via gTTS
    4. Return audio/mpeg blob for auto-play in the browser
    """
    import urllib.parse
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        logger.info(f"[chat/voice] user={current_user.id} file={file.filename!r}, size={len(audio_bytes)}")

        # ---- Step 1: STT via Gemini ----------------------------------------
        transcript = await _transcribe_audio(audio_bytes, file.content_type or "audio/webm", language)
        logger.info(f"[chat/voice] transcript={transcript!r}")

        if not transcript or transcript.strip() == "":
            transcript = "Could not understand audio, please try again."

        # ---- Step 2: Route to Orchestrator (with real user_id) ---------------
        extra = {"session_id": session_id} if session_id else None
        orch_result = await _call_orchestrator(transcript, user_id=current_user.id, extra=extra)
        text_response = orch_result.get("response", "I processed your request.")

        # Save history if session_id provided
        if session_id:
            try:
                from farmxpert.interfaces.api.routes.super_agent import _db_save_message
                _db_save_message(session_id, "user", f"[🎤 Voice] {transcript}", user_id=current_user.id)
                _db_save_message(session_id, "assistant", text_response, user_id=current_user.id)
            except Exception as e:
                logger.warning(f"Failed to save voice chat history: {e}")

        # ---- Step 3: TTS via gTTS -------------------------------------------
        audio_mp3 = await _text_to_speech(text_response, language or "en")

        # ---- Step 4: Return audio stream ------------------------------------
        return Response(
            content=audio_mp3,
            media_type="audio/mpeg",
            headers={
                "X-Transcript": urllib.parse.quote(transcript[:500]),
                "X-Text-Response": urllib.parse.quote(text_response[:500]),
                "Access-Control-Expose-Headers": "X-Transcript, X-Text-Response",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[chat/voice] error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


async def _transcribe_audio(audio_bytes: bytes, content_type: str, language: Optional[str]) -> str:
    """Use Gemini's multimodal capability to transcribe audio."""
    import asyncio
    try:
        model = _get_gemini_model("gemini-1.5-flash")
        lang_hint = f" The speaker is speaking in {language}." if language and language != "en" else ""
        prompt = f"Transcribe the speech in this audio file exactly as spoken.{lang_hint} Return only the transcribed text, nothing else."

        # Gemini can process inline audio data
        audio_part = {"mime_type": content_type, "data": audio_bytes}
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, [prompt, audio_part]),
            timeout=30,
        )
        try:
            return response.text.strip()
        except Exception:
            return response.candidates[0].content.parts[0].text.strip()
    except Exception as e:
        logger.warning(f"[chat/voice] Gemini STT failed: {e}, using placeholder")
        return ""


async def _text_to_speech(text: str, language: str = "en") -> bytes:
    """Convert text to MP3 bytes using gTTS."""
    import asyncio
    try:
        from gtts import gTTS  # type: ignore
        tts = gTTS(text=text[:3000], lang=language, slow=False)
        buf = io.BytesIO()
        await asyncio.to_thread(tts.write_to_fp, buf)
        buf.seek(0)
        return buf.read()
    except ImportError:
        logger.error("[chat/voice] gTTS not installed. Add gTTS to requirements.txt")
        raise HTTPException(
            status_code=503,
            detail="TTS service (gTTS) is not installed. Run: pip install gTTS",
        )
    except Exception as e:
        logger.error(f"[chat/voice] TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


# ===========================================================================
# PHASE 5 — POST /api/chat/document (PDF/CSV/TXT → Gemini document analysis)
# ===========================================================================

@router.post("/document")
async def chat_document(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(..., description="PDF, CSV, or TXT document"),
    prompt: Optional[str] = Form(None, description="What to analyze or ask about the document"),
    session_id: Optional[str] = Form(None),
):
    """
    Upload a PDF, CSV, or TXT file and receive an AI-powered analysis
    (requires authentication). Ideal for soil lab reports, insurance
    documents, crop records, etc.

    Gemini 1.5 Flash supports native PDF parsing.
    """
    import asyncio
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        filename = file.filename or "document"
        content_type = file.content_type or _guess_mime(filename)
        logger.info(f"[chat/document] user={current_user.id} file={filename!r}, size={len(file_bytes)}, type={content_type}")

        user_prompt = prompt or "Analyze this agricultural document and extract key insights."

        analysis_prompt = f"""You are an expert agricultural data analyst.
The user has uploaded a document named "{filename}".

User question / task: {user_prompt}

Please analyze the document and provide:
1. A concise summary of what the document contains
2. Key values (e.g., NPK levels, soil pH, recommendations, financial details)
3. Actionable insights and recommendations for the farmer
4. Any alerts or warnings based on the data

Format your response clearly with sections and bullet points where appropriate."""

        model = _get_gemini_model("gemini-1.5-flash")
        doc_part = {"mime_type": content_type, "data": file_bytes}

        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, [analysis_prompt, doc_part]),
            timeout=60,
        )
        try:
            analysis_text = response.text
        except Exception:
            analysis_text = response.candidates[0].content.parts[0].text

        if session_id:
            try:
                from farmxpert.interfaces.api.routes.super_agent import _db_save_message
                user_msg = f"[📎 {filename}] {user_prompt}".strip()
                _db_save_message(session_id, "user", user_msg, user_id=current_user.id)
                _db_save_message(session_id, "assistant", analysis_text, user_id=current_user.id)
            except Exception as e:
                logger.warning(f"Failed to save document chat history: {e}")

        return {
            "success": True,
            "response": analysis_text,
            "filename": filename,
            "content_type": content_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[chat/document] error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# ===========================================================================
# Utilities
# ===========================================================================

def _parse_json_safe(text: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON from a Gemini response that may be wrapped in markdown."""
    if not text:
        return None
    # Strip markdown code fences
    cleaned = text.strip()
    for fence in ("```json", "```JSON", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
            break
    cleaned = cleaned.rstrip("`").strip()

    # Find JSON object bounds
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        return None


def _guess_mime(filename: str) -> str:
    """Guess MIME type from file extension."""
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "pdf": "application/pdf",
        "csv": "text/csv",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")


# Health check
@router.get("/health")
async def chat_health():
    return {
        "status": "ok",
        "endpoints": ["orchestrate", "vision", "voice", "document"],
        "gemini_configured": bool(settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")),
        "timestamp": datetime.utcnow().isoformat(),
    }
