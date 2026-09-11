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

def _get_gemini_model(model_name: Optional[str] = None):
    """Return a configured Gemini GenerativeModel."""
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Do not raise here; caller should handle missing model gracefully.
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)
    chosen_model = model_name or getattr(settings, "gemini_model", "gemini-2.5-flash") or "gemini-2.5-flash"
    return genai.GenerativeModel(chosen_model)


# ---------------------------------------------------------------------------
# Helper: call orchestrator and format response
# ---------------------------------------------------------------------------

async def _call_orchestrator(message: str, user_id: int, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call SuperAgent and return a clean response dict.

    This helper now catches internal exceptions and returns a structured
    response object rather than letting exceptions bubble up to the HTTP layer.
    """
    from farmxpert.core.super_agent import super_agent

    payload: Dict[str, Any] = {
        "query": message,
        "user_id": str(user_id),
        "context": extra or {}
    }

    try:
        result = await super_agent.process_query(
            query=message,
            context=payload,
            session_id=extra.get("session_id") if extra else None
        )

        # Extract the best human-readable text from the result
        # Guard against unexpected shapes by using .get with defaults
        response_text = ""
        try:
            if isinstance(result, dict):
                response_text = result.get("natural_language") or (result.get("response", {}).get("response") if isinstance(result.get("response"), dict) else result.get("response", ""))
            else:
                response_text = getattr(result, 'natural_language', None) or (getattr(result, 'response', {}).get('response') if getattr(result, 'response', None) else '')
        except Exception:
            response_text = str(result)

        # Build agent_responses list for the frontend chips
        agent_responses = []
        try:
            for agent_response in getattr(result, 'agent_responses', []) or result.get('agent_responses', []) or []:
                agent_responses.append({
                    "agent_name": getattr(agent_response, 'agent_name', agent_response.get('agent_name') if isinstance(agent_response, dict) else None),
                    "success": getattr(agent_response, 'success', agent_response.get('success') if isinstance(agent_response, dict) else True),
                    "summary": (agent_response.data.get('response', '')[:100] + "...") if getattr(agent_response, 'success', True) and hasattr(agent_response, 'data') else (agent_response.get('summary') if isinstance(agent_response, dict) else None),
                })
        except Exception:
            agent_responses = []

        return {
            "success": getattr(result, 'success', result.get('success') if isinstance(result, dict) else False),
            "response": response_text,
            "query_type": "super_agent",
            "agent_responses": agent_responses,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"_call_orchestrator failed: {e}", exc_info=True)
        # Return a structured failure result so callers can display the backend message
        return {
            "success": False,
            "response": "The orchestrator encountered an internal error while processing your request.",
            "error": str(e),
            "query_type": "super_agent",
            "agent_responses": [],
            "timestamp": datetime.utcnow().isoformat(),
        }


# ===========================================================================
# PHASE 1 — POST /api/chat/orchestrate (Text Chat)
# ===========================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    farm_id: Optional[int] = None
    user_id: Optional[int] = None # Optional; authenticated user is always derived securely from auth token
    context: Optional[Dict[str, Any]] = None


@router.post("")
@router.post("/")
@router.post("/orchestrate")
async def chat_orchestrate(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unified chat endpoint (requires authentication).
    Uses FarmXpertOrchestrator with explicit intent routing, authenticated
    farm context resolution, real tool calling, and strict response scope control.
    """
    try:
        logger.info(f"[chat] user={current_user.id} message={request.message[:80]!r}")
        session_id = request.session_id or str(uuid.uuid4())

        # Extract chat history for conversational context
        chat_history = []
        try:
            from farmxpert.interfaces.api.routes.super_agent import _db_get_history
            chat_history = _db_get_history(session_id, user_id=current_user.id)
        except Exception as e:
            logger.warning(f"Failed to fetch chat history context: {e}")

        # Execute through FarmXpert Master Orchestrator
        from farmxpert.services.orchestrator.farmxpert_orchestrator import farmxpert_orchestrator

        try:
            orch_res = await farmxpert_orchestrator.process_request(
                message=request.message,
                user=current_user,
                db=db,
                session_id=session_id,
                requested_farm_id=request.farm_id,
                chat_history=chat_history[-10:] if chat_history else []
            )
        except Exception as e:
            # Catch internal orchestrator errors and return a structured JSON instead of raising 500
            logger.error(f"Orchestrator processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "response": "The farm orchestrator failed to process your request. Please try again later.",
                "error": str(e),
                "agent_responses": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Build agent_responses list for frontend active chips (ChatPanel.jsx)
        agent_responses = []
        if orch_res.get("agent"):
            agent_responses.append({
                "agent_name": orch_res.get("agent"),
                "success": orch_res.get("success", True),
                "summary": orch_res.get("response", "")[:100] + "..." if len(orch_res.get("response", "")) > 100 else orch_res.get("response", "")
            })
        orch_res["agent_responses"] = agent_responses

        # Save to chat history
        try:
            from farmxpert.interfaces.api.routes.super_agent import _db_save_message
            _db_save_message(session_id, "user", request.message, user_id=current_user.id)
            _db_save_message(session_id, "assistant", orch_res.get("response", ""), user_id=current_user.id)
        except Exception as e:
            logger.warning(f"Failed to save chat history: {e}")

        return orch_res

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[chat] error: {e}", exc_info=True)
        # Return structured JSON rather than raw HTTPException detail
        return {
            "success": False,
            "response": "Internal server error while handling chat request.",
            "error": str(e),
        }


@router.get("/debug")
async def chat_debug(
    query: str,
    farm_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Observability & Debug Endpoint (STEP 25).
    Shows structured execution trace: User Request -> Intent -> Agent -> Context -> Tool Calls -> Response.
    Never reveals private reasoning or credentials.
    """
    from farmxpert.services.orchestrator.farmxpert_orchestrator import farmxpert_orchestrator
    res = await farmxpert_orchestrator.process_request(
        message=query,
        user=current_user,
        db=db,
        session_id="debug_session",
        requested_farm_id=farm_id
    )
    return {
        "user_request": query,
        "resolved_intent": res.get("intent"),
        "selected_agent": res.get("agent"),
        "context_used": res.get("context_used"),
        "tools_executed": res.get("tool_calls"),
        "final_response": res.get("response"),
        "duration_ms": res.get("duration_ms")
    }


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

        model = _get_gemini_model()
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
        model = _get_gemini_model()
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

        model = _get_gemini_model()
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
