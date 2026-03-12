"""
Voice Chat Router
Unified endpoint: audio in → STT → orchestrator → TTS → audio out
"""

import os
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
from datetime import datetime

from farmxpert.voice.stt_service import transcribe
from farmxpert.voice.tts_service import generate_speech, AUDIO_OUTPUT_DIR, cleanup_old_audio
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.models.user_models import User
from farmxpert.interfaces.api.routes.chat_routes import _call_orchestrator
from fastapi import Depends

logger = logging.getLogger("voice.router")

router = APIRouter(prefix="/voice", tags=["Voice Agent"])


@router.post("/chat")
async def voice_chat(
    audio: UploadFile = File(..., description="Audio file (wav, webm, mp3)"),
    language: Optional[str] = Form(None, description="Language hint (e.g., 'hi' for Hindi). Auto-detected if omitted."),
    current_user: User = Depends(get_current_user),
):
    """
    Unified voice chat endpoint.

    Flow:
    1. Receive audio file from frontend
    2. STT: Convert speech → text (auto-detect language)
    3. Forward text to orchestrator
    4. TTS: Convert response → speech audio
    5. Return transcript, response text, and audio URL

    Returns:
        {
            "transcript": "user's spoken text",
            "response": "AI response text",
            "audio_url": "/api/voice/audio/filename.mp3",
            "detected_language": "hi",
            "language_name": "Hindi"
        }
    """
    try:
        # Step 1: Read uploaded audio
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")

        logger.info(f"Voice chat: received {len(audio_bytes)} bytes, content_type={audio.content_type}")

        # Step 2: Speech-to-Text
        stt_result = await transcribe(audio_bytes, language=language)

        if not stt_result["success"] or not stt_result.get("transcript"):
            return JSONResponse(
                status_code=200,
                content={
                    "transcript": "",
                    "response": "I couldn't understand the audio. Please try speaking again more clearly.",
                    "audio_url": None,
                    "detected_language": stt_result.get("detected_language"),
                    "language_name": stt_result.get("language_name"),
                    "error": stt_result.get("error"),
                },
            )

        transcript = stt_result["transcript"]
        detected_language = stt_result.get("detected_language", "en")
        language_name = stt_result.get("language_name", "English")

        logger.info(f"STT result: '{transcript[:100]}...' (lang={detected_language})")

        # Step 3: Forward to orchestrator
        try:
            from farmxpert.app.orchestrator.agent import OrchestratorAgent

            orchestrator_result = await OrchestratorAgent.handle_request({
                "query": transcript,
                "strategy": "auto",
            })

            if orchestrator_result.get("error"):
                response_text = "I'm sorry, I encountered an error processing your request. Please try again."
                logger.error(f"Orchestrator error: {orchestrator_result}")
            else:
                # Extract the response text from orchestrator
                response_text = (
                    orchestrator_result.get("llm_summary")
                    or orchestrator_result.get("summary")
                    or orchestrator_result.get("response")
                    or str(orchestrator_result)
                )
        except Exception as e:
            logger.error(f"Orchestrator call failed: {e}")
            response_text = "I'm having trouble connecting to the farm system. Please try again in a moment."

        logger.info(f"Orchestrator response: '{response_text[:100]}...'")

        # Step 4: Text-to-Speech
        tts_result = await generate_speech(
            text=response_text,
            language=detected_language,
        )

        audio_url = None
        if tts_result["success"] and tts_result.get("audio_filename"):
            audio_url = f"/api/voice/audio/{tts_result['audio_filename']}"

        # Step 5: Cleanup old files periodically
        try:
            cleanup_old_audio(max_age_seconds=1800)  # 30 minutes
        except Exception:
            pass

        # Step 6: Return response
        return {
            "transcript": transcript,
            "response": response_text,
            "audio_url": audio_url,
            "detected_language": detected_language,
            "language_name": language_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


@router.post("/text-chat")
async def voice_text_chat(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Text-based voice chat endpoint.
    Used when browser Web Speech API handles STT client-side.

    Request body:
        {
            "text": "user's spoken text",
            "language": "en"  (optional)
        }

    Returns:
        {
            "response": "AI response text",
            "audio_url": "/api/voice/audio/filename.mp3",
            "agent_responses": [...]
        }
    """
    try:
        text = request.get("text", "").strip()
        language = request.get("language", "en")

        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        logger.info(f"Voice text-chat: '{text[:100]}' (lang={language}, user={current_user.id})")

        # Step 1: Forward to orchestrator using the shared chat_routes helper
        agent_responses = []
        try:
            orch_result = await _call_orchestrator(text, user_id=current_user.id)
            response_text = orch_result.get("response", "I processed your request.")
            agent_responses = orch_result.get("agent_responses", [])
        except Exception as e:
            logger.error(f"Orchestrator call failed: {e}")
            response_text = "I'm having trouble connecting to the farm system. Please try again in a moment."

        # Step 2: Text-to-Speech
        tts_result = await generate_speech(
            text=response_text,
            language=language,
        )

        audio_url = None
        if tts_result["success"] and tts_result.get("audio_filename"):
            audio_url = f"/api/voice/audio/{tts_result['audio_filename']}"

        # Cleanup old files
        try:
            cleanup_old_audio(max_age_seconds=1800)
        except Exception:
            pass

        return {
            "response": response_text,
            "audio_url": audio_url,
            "agent_responses": agent_responses,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice text-chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve a generated audio file."""
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(AUDIO_OUTPUT_DIR, safe_filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=safe_filename,
    )


@router.get("/status")
async def voice_status():
    """Health check for voice services."""
    stt_ready = False
    tts_ready = False

    try:
        from faster_whisper import WhisperModel  # noqa: F401
        stt_ready = True
    except ImportError:
        pass

    try:
        from gtts import gTTS  # noqa: F401
        tts_ready = True
    except ImportError:
        pass

    return {
        "status": "healthy" if (stt_ready and tts_ready) else "degraded",
        "stt": {
            "provider": "faster-whisper",
            "ready": stt_ready,
            "languages": ["en", "hi", "gu", "ta", "te", "mr", "bn", "pa", "kn", "ml"],
        },
        "tts": {
            "provider": "gTTS",
            "ready": tts_ready,
            "languages": ["en", "hi", "gu", "ta", "te", "mr", "bn", "pa", "kn", "ml"],
        },
    }
