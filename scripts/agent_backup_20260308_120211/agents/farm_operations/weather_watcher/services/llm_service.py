import os
from loguru import logger
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from ..models.output_models import WeatherAlertOutput

# Google Gen AI (new package)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    try:
        # Fallback to deprecated package
        import google.generativeai as genai
        GENAI_AVAILABLE = True
        logger.warning("⚠️ Using deprecated google.generativeai package. Consider upgrading to google.genai")
    except ImportError:
        GENAI_AVAILABLE = False
        logger.warning("⚠️ Google Gen AI not available")

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️ OpenAI not available")

# Use app configuration
from app.config import settings

# ---------- API SETUP ---------- #

# Load project-level .env for backward compatibility
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_PROJECT_ROOT / ".env")

# Use settings for API keys
GOOGLE_API_KEY = settings.google_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

# Initialize clients
if GENAI_AVAILABLE and GOOGLE_API_KEY:
    try:
        if hasattr(genai, 'configure'):
            genai.configure(api_key=GOOGLE_API_KEY)
        else:
            # For deprecated package
            import google.generativeai as genai_old
            genai_old.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"❌ Failed to configure Google Gen AI: {e}")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_AVAILABLE and OPENAI_API_KEY else None

_GEMINI_MODEL_NAME: Optional[str] = None


# ---------- PROMPT TEMPLATE ---------- #

SYSTEM_PROMPT = """
You are FarmXpert Weather Assistant.

Rules:
- Explain alerts clearly and calmly
- Do NOT invent weather data
- Do NOT change severity or actions
- Always mention confidence
- Use simple language suitable for farmers
- No emojis, no exaggeration
"""

USER_PROMPT_TEMPLATE = """
Alert Type: {alert_type}
Severity: {severity}
Confidence: {confidence}
Message: {message}

Recommended Actions:
{actions}

Explain this alert to a farmer in 3–4 short sentences.
"""


class LLMService:
    """
    Handles alert explanation using Gemini (primary) and ChatGPT (fallback)
    """

    @staticmethod
    def explain_alert(alert: WeatherAlertOutput) -> str:
        prompt = LLMService._build_prompt(alert)

        explanation = LLMService._call_gemini(prompt)
        if explanation:
            return explanation

        logger.warning("⚠️ Gemini failed, switching to ChatGPT")
        explanation = LLMService._call_chatgpt(prompt)

        if explanation:
            return explanation

        logger.error("❌ All LLMs failed, using static fallback")
        return LLMService._static_fallback(alert)

    # ---------- INTERNAL ---------- #

    @staticmethod
    def _build_prompt(alert: WeatherAlertOutput) -> str:
        actions_text = "\n".join(
            f"- {a.action}" for a in alert.actions
        )

        return USER_PROMPT_TEMPLATE.format(
            alert_type=alert.alert_type,
            severity=alert.severity,
            confidence=alert.confidence,
            message=alert.message,
            actions=actions_text
        )

    # ---------- GEMINI ---------- #

    @staticmethod
    def _call_gemini(prompt: str) -> Optional[str]:
        try:
            if not GENAI_AVAILABLE or not GOOGLE_API_KEY:
                return None

            global _GEMINI_MODEL_NAME
            if not _GEMINI_MODEL_NAME:
                try:
                    # Try to get model name for new package
                    if hasattr(genai, 'list_models'):
                        models = genai.list_models()
                        for model in models:
                            if hasattr(model, 'supported_generation_methods'):
                                methods = model.supported_generation_methods or []
                                if "generateContent" in methods:
                                    _GEMINI_MODEL_NAME = model.name
                                    break
                    else:
                        # For deprecated package
                        import google.generativeai as genai_old
                        for m in genai_old.list_models():
                            methods = getattr(m, "supported_generation_methods", None) or []
                            if "generateContent" in methods:
                                _GEMINI_MODEL_NAME = m.name
                                break
                except Exception as e:
                    logger.error(f"❌ Gemini model discovery error: {e}")
                    # Use default model name
                    _GEMINI_MODEL_NAME = "models/gemini-pro"

            if not _GEMINI_MODEL_NAME:
                _GEMINI_MODEL_NAME = "models/gemini-pro"

            # Try new package first
            if hasattr(genai, 'GenerativeModel'):
                model = genai.GenerativeModel(
                    model_name=_GEMINI_MODEL_NAME,
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(prompt)
                if getattr(response, "text", None):
                    return response.text.strip()
            else:
                # Fallback to deprecated package
                import google.generativeai as genai_old
                model = genai_old.GenerativeModel(
                    model_name=_GEMINI_MODEL_NAME,
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(prompt)
                if getattr(response, "text", None):
                    return response.text.strip()

            return None

        except Exception as e:
            logger.error(f"❌ Gemini error: {e}")
            return None

    # ---------- CHATGPT ---------- #

    @staticmethod
    def _call_chatgpt(prompt: str) -> Optional[str]:
        try:
            if not openai_client:
                return None
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"❌ ChatGPT error: {e}")
            return None

    # ---------- FALLBACK ---------- #

    @staticmethod
    def _static_fallback(alert: WeatherAlertOutput) -> str:
        return (
            f"{alert.message} "
            f"Please follow the recommended actions. "
            f"Confidence level: {alert.confidence}."
        )
