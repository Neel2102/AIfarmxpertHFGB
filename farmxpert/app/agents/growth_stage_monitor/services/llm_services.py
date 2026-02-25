import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from ..models.output_models import (
    GrowthStageAssessment,
    GrowthHealthStatus,
    GrowthAlert
)

# Gemini
import google.generativeai as genai

# OpenAI
from openai import OpenAI


# ---------------- API SETUP ---------------- #

# Load project-level .env so running from subfolders still picks up keys
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

_GEMINI_MODEL_NAME: Optional[str] = None


# ---------------- PROMPTS ---------------- #

SYSTEM_PROMPT = """
You are FarmXpert Growth Assistant.

Rules:
- Explain observations calmly
- Do NOT diagnose diseases
- Do NOT suggest chemicals
- Do NOT exaggerate risks
- Use simple farmer-friendly language
- Encourage monitoring and follow-up images
"""

USER_PROMPT_TEMPLATE = """
Crop: {crop}
Current Stage: {stage}
Stage Confidence: {stage_confidence}

Growth Status: {status}
Reason: {reason}

Alert:
Type: {alert_type}
Severity: {severity}
Confidence: {alert_confidence}
Message: {alert_message}

Explain this to a farmer in 3–4 short sentences.
Include what they should do next (monitoring only).
"""


class GrowthLLMService:

    @staticmethod
    def explain_growth_alert(
        crop_name: str,
        stage: GrowthStageAssessment,
        health: GrowthHealthStatus,
        alert: GrowthAlert
    ) -> str:
        print(f"\n🤖 LLM EXPLANATION GENERATION")
        print(f"┌{'─'*18}┬{'─'*15}┬{'─'*25}┐")
        print(f"│{'Component':^18}│{'Provider':^15}│{'Status':^25}│")
        print(f"├{'─'*18}┼{'─'*15}┼{'─'*25}┤")

        # Try Gemini first
        if GEMINI_API_KEY:
            print(f"│{'Primary LLM':^18}│{'Gemini':^15}│{'Attempting...':^25}│")
            try:
                prompt = GrowthLLMService._build_prompt(crop_name, stage, health, alert)
                explanation = GrowthLLMService._call_gemini(prompt)
                print(f"│{'Primary LLM':^18}│{'Gemini':^15}│{'✅ Success':^25}│")
                print(f"└{'─'*18}┴{'─'*15}┴{'─'*25}┘")
                return explanation
            except Exception as e:
                print(f"│{'Primary LLM':^18}│{'Gemini':^15}│{'❌ Failed':^25}│")
                logger.warning(f"Gemini LLM failed: {e}")
        else:
            print(f"│{'Primary LLM':^18}│{'Gemini':^15}│{'❌ No API Key':^25}│")

        # Fallback to OpenAI
        if openai_client:
            print(f"│{'Fallback LLM':^18}│{'OpenAI':^15}│{'Attempting...':^25}│")
            try:
                prompt = GrowthLLMService._build_prompt(crop_name, stage, health, alert)
                explanation = GrowthLLMService._call_chatgpt(prompt)
                print(f"│{'Fallback LLM':^18}│{'OpenAI':^15}│{'✅ Success':^25}│")
                print(f"└{'─'*18}┴{'─'*15}┴{'─'*25}┘")
                return explanation
            except Exception as e:
                print(f"│{'Fallback LLM':^18}│{'OpenAI':^15}│{'❌ Failed':^25}│")
                logger.warning(f"OpenAI LLM failed: {e}")
        else:
            print(f"│{'Fallback LLM':^18}│{'OpenAI':^15}│{'❌ No API Key':^25}│")

        # Static fallback
        print(f"│{'Static Response':^18}│{'Built-in':^15}│{'✅ Success':^25}│")
        print(f"└{'─'*18}┴{'─'*15}┴{'─'*25}┘")
        return GrowthLLMService._static_fallback(stage, health)

    # ---------------- INTERNAL ---------------- #

    @staticmethod
    def _build_prompt(crop, stage, health, alert) -> str:
        return USER_PROMPT_TEMPLATE.format(
            crop=crop,
            stage=stage.current_stage,
            stage_confidence=stage.confidence,
            status=health.status,
            reason=health.reason,
            alert_type=alert.alert_type,
            severity=alert.severity,
            alert_confidence=alert.confidence,
            alert_message=alert.message
        )

    # ---------------- GEMINI ---------------- #

    @staticmethod
    def _call_gemini(prompt: str) -> Optional[str]:
        try:
            if not GEMINI_API_KEY:
                return None

            global _GEMINI_MODEL_NAME
            if not _GEMINI_MODEL_NAME:
                try:
                    for m in genai.list_models():
                        methods = getattr(m, "supported_generation_methods", None) or []
                        if "generateContent" in methods:
                            _GEMINI_MODEL_NAME = m.name
                            break
                except Exception as e:
                    logger.error(f"❌ Gemini model discovery error: {e}")
                    return None

            if not _GEMINI_MODEL_NAME:
                return None

            model = genai.GenerativeModel(
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

    # ---------------- CHATGPT ---------------- #

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

    # ---------------- FALLBACK ---------------- #

    @staticmethod
    def _static_fallback(stage, health) -> str:
        return (
            f"Your crop is currently in the {stage.current_stage} stage. "
            f"Growth appears slightly slower than expected. "
            f"Please monitor the crop closely and upload clear images again in a few days."
        )
