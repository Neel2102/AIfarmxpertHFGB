"""
Speech-to-Text Service using Faster-Whisper
Supports multilingual speech recognition including Indian languages:
Hindi, Gujarati, Tamil, Telugu, Marathi, Bengali, English, and more.
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("voice.stt")

# Lazy-loaded model instance
_model = None


def _get_model():
    """Lazy-load the Faster-Whisper model on first use."""
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
            logger.info(f"Loading Faster-Whisper model: {model_size} on {device} ({compute_type})")
            _model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("Faster-Whisper model loaded successfully")
        except ImportError:
            logger.error("faster-whisper not installed. Run: pip install faster-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _model


# Map Whisper language codes to human-readable names
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "ur": "Urdu",
    "as": "Assamese",
}


async def transcribe(audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio bytes to text using Faster-Whisper.

    Args:
        audio_bytes: Raw audio file bytes (wav, webm, mp3, etc.)
        language: Optional language code to force (e.g., 'hi' for Hindi).
                  If None, language is auto-detected.

    Returns:
        Dict with keys: success, transcript, detected_language, language_name, error
    """
    tmp_path = None
    try:
        # Write audio to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()

        # Transcribe with optional language hint
        transcribe_kwargs = {"beam_size": 5, "vad_filter": True}
        if language:
            transcribe_kwargs["language"] = language

        segments, info = model.transcribe(tmp_path, **transcribe_kwargs)

        # Collect all segment texts
        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())

        transcript = " ".join(transcript_parts).strip()
        detected_lang = info.language if info else (language or "en")
        language_name = LANGUAGE_MAP.get(detected_lang, detected_lang)

        logger.info(f"STT result: lang={detected_lang} ({language_name}), "
                     f"probability={info.language_probability:.2f}, "
                     f"transcript_length={len(transcript)}")

        return {
            "success": True,
            "transcript": transcript,
            "detected_language": detected_lang,
            "language_name": language_name,
            "language_probability": round(info.language_probability, 2) if info else 0.0,
            "error": None,
        }

    except Exception as e:
        logger.error(f"STT transcription failed: {e}")
        return {
            "success": False,
            "transcript": None,
            "detected_language": None,
            "language_name": None,
            "error": str(e),
        }
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
