"""
Text-to-Speech Service using gTTS
Supports multilingual speech synthesis including Indian languages:
Hindi, Gujarati, Tamil, Telugu, Marathi, Bengali, English, and more.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("voice.tts")

# Directory for generated audio files
AUDIO_OUTPUT_DIR = os.getenv("VOICE_AUDIO_DIR", "/tmp/voice_audio")

# Language code mapping for gTTS
# gTTS uses standard language codes
GTTS_LANGUAGE_MAP = {
    "en": "en",
    "hi": "hi",
    "gu": "gu",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
    "bn": "bn",
    "pa": "pa",
    "kn": "kn",
    "ml": "ml",
    "or": "or",  # Note: gTTS may not support all codes
    "ur": "ur",
    "as": "as",
}


def _ensure_output_dir():
    """Create the audio output directory if it doesn't exist."""
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)


async def generate_speech(
    text: str,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate speech audio from text using gTTS.

    Args:
        text: Text to convert to speech.
        language: Language code (e.g., 'hi' for Hindi). Defaults to 'en'.

    Returns:
        Dict with keys: success, audio_filename, audio_path, language_used, error
    """
    try:
        from gtts import gTTS

        _ensure_output_dir()

        # Resolve language code
        lang_code = GTTS_LANGUAGE_MAP.get(language, "en") if language else "en"

        # Generate unique filename
        audio_filename = f"voice_{uuid.uuid4().hex[:12]}.mp3"
        audio_path = os.path.join(AUDIO_OUTPUT_DIR, audio_filename)

        logger.info(f"TTS: generating speech in '{lang_code}' for text length={len(text)}")

        # Generate speech
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(audio_path)

        logger.info(f"TTS: saved audio to {audio_path}")

        return {
            "success": True,
            "audio_filename": audio_filename,
            "audio_path": audio_path,
            "language_used": lang_code,
            "error": None,
        }

    except ValueError as e:
        # gTTS raises ValueError for unsupported languages
        logger.warning(f"TTS language '{language}' not supported, falling back to English: {e}")
        try:
            from gtts import gTTS

            _ensure_output_dir()
            audio_filename = f"voice_{uuid.uuid4().hex[:12]}.mp3"
            audio_path = os.path.join(AUDIO_OUTPUT_DIR, audio_filename)

            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(audio_path)

            return {
                "success": True,
                "audio_filename": audio_filename,
                "audio_path": audio_path,
                "language_used": "en",
                "error": None,
            }
        except Exception as fallback_error:
            logger.error(f"TTS fallback also failed: {fallback_error}")
            return {
                "success": False,
                "audio_filename": None,
                "audio_path": None,
                "language_used": None,
                "error": str(fallback_error),
            }

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return {
            "success": False,
            "audio_filename": None,
            "audio_path": None,
            "language_used": None,
            "error": str(e),
        }


def cleanup_old_audio(max_age_seconds: int = 3600):
    """Remove audio files older than max_age_seconds."""
    import time

    try:
        if not os.path.exists(AUDIO_OUTPUT_DIR):
            return

        now = time.time()
        for filename in os.listdir(AUDIO_OUTPUT_DIR):
            filepath = os.path.join(AUDIO_OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                age = now - os.path.getmtime(filepath)
                if age > max_age_seconds:
                    os.unlink(filepath)
                    logger.debug(f"Cleaned up old audio file: {filename}")
    except Exception as e:
        logger.warning(f"Audio cleanup error: {e}")
