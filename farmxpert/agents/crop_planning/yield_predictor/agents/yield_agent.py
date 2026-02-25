# agents/yield_agent.py
import sys
from pathlib import Path
import os
import re
import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool
import google.generativeai as genai
from langchain_core.messages import AIMessage

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from tools.soil_tool import get_soil_data
from tools.whether_tool import get_weather_data
from tools.yield_predictor_tool import YieldPredictionInput, yield_predictor_tool

# Load .env file
load_dotenv()

# Now keys are available as environment variables
GEMINI_API_KEY = os.getenv("GEMINIAPI") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in .env (expected GEMINIAPI or GOOGLE_API_KEY)")


def _resolve_gemini_model() -> str:
    if GEMINI_MODEL:
        return GEMINI_MODEL

    # Try to pick a supported model for the user's API project.
    # We avoid hardcoding one model name because availability differs by account/API version.
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        available = [m.name for m in genai.list_models()]
    except Exception:
        available = []

    # Prefer models that support generation.
    candidates = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro",
    ]

    if available:
        # genai returns names like "models/gemini-1.5-pro"; ChatGoogleGenerativeAI expects without "models/".
        cleaned = [a.replace("models/", "") for a in available]
        for c in candidates:
            if c in cleaned:
                return c
        # If none matched, pick the first gemini model.
        for name in cleaned:
            if name.startswith("gemini"):
                return name

    # Last resort: use a conservative default and let the next call surface a clear error.
    return "gemini-pro"

soil_tool = StructuredTool.from_function(
    func=get_soil_data,
    name="SoilData",
    description="Fetches soil properties for a given location",
)

weather_tool = StructuredTool.from_function(
    func=get_weather_data,
    name="WeatherData",
    description="Fetches weather data for a given location and year",
)

ml_tool = StructuredTool.from_function(
    func=yield_predictor_tool,
    name="YieldPrediction",
    description="Predicts crop yield given State_Name, District_Name, Crop, Season, Crop_Year, and Area. Input must be JSON. Production must not be provided.",
    args_schema=YieldPredictionInput,
)

# Initialize chat model (Gemini via LangChain)
llm = ChatGoogleGenerativeAI(model=_resolve_gemini_model(), temperature=0, google_api_key=GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a Yield Predictor Agent for agriculture. "
    "You MUST ONLY handle agriculture/yield-related requests (crop yield prediction, and brief help about required inputs). "
    "If the user asks for anything else (math, general Q&A, news, jokes, coding, etc.), refuse with a short message like: "
    "'I can only help with crop yield prediction and related agriculture questions.' "
    "When the user asks for a yield prediction, you MUST call the YieldPrediction tool. "
    "Required fields: State_Name, District_Name, Crop, Season, Crop_Year, Area. "
    "If Crop_Year or Area is missing, ask for them briefly. "
    "In follow-up questions like 'same for Punjab' or 'same for another district', reuse the most recent Crop, Season, Crop_Year and Area from the conversation, and ask ONLY for the missing location fields (usually District_Name). "
    "Do not mention internal logs or tool schemas. Return clear, short answers."
)


def get_agent(verbose: bool = False):
    return create_agent(
        llm,
        tools=[soil_tool, weather_tool, ml_tool],
        system_prompt=_SYSTEM_PROMPT,
        debug=verbose,
        name="YieldPredictorAgent",
    )


def _message_to_text(msg) -> str:
    if isinstance(msg, AIMessage):
        content = msg.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, dict) and p.get("type") == "text":
                    parts.append(str(p.get("text", "")))
            joined = "\n".join([t for t in parts if t])
            return joined if joined else str(content)
        return str(content)
    return getattr(msg, "content", str(msg))


def _is_supported_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True

    # Allow asking about agent capabilities.
    if any(k in t for k in ["what can you do", "help", "how to use", "usage"]):
        return True

    # Obvious non-agri topics.
    if any(k in t for k in ["news", "headline", "today's news", "stock", "weather in"]):
        # weather queries should use WeatherData tool but current implementation expects lat/lon;
        # keep scope tight and treat general 'weather in <city>' as unsupported.
        return False

    # Simple math expressions (e.g., 5+5, 2 + 2, 10/3).
    if re.fullmatch(r"[0-9\s\+\-\*\/\(\)\.]+", t):
        return False

    agri_keywords = [
        "yield",
        "crop",
        "wheat",
        "rice",
        "maize",
        "cotton",
        "season",
        "rabi",
        "kharif",
        "zaid",
        "district",
        "state",
        "hectare",
        "area",
        "production",
        "soil",
    ]
    return any(k in t for k in agri_keywords)


def _load_demo_request_json() -> str:
    demo_path = _ROOT / "demo_yield_request.json"
    with open(demo_path, "r", encoding="utf-8") as f:
        return f.read()


def _looks_like_json_object(text: str) -> bool:
    t = (text or "").strip()
    return t.startswith("{") and t.endswith("}")


def _as_json_response(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _build_agent_prompt_from_user_input(user_text: str) -> str:
    t = (user_text or "").strip()

    t_lower = t.lower()

    if not t:
        demo_json = _load_demo_request_json().strip()
        return (
            "Predict crop yield using the following input JSON (do not ask questions; just run the tool):\n"
            f"{demo_json}"
        )

    if t_lower in {"give update", "update", "demo", "sample"}:
        demo_json = _load_demo_request_json().strip()
        return (
            "Predict crop yield using the following input JSON (do not ask questions; just run the tool):\n"
            f"{demo_json}"
        )

    if _looks_like_json_object(t):
        try:
            json.loads(t)
        except json.JSONDecodeError:
            return (
                "The JSON you provided is not valid. Please provide a valid JSON object with keys "
                "State_Name, District_Name, Crop, Season, Crop_Year, Area."
            )
        return (
            "Predict crop yield using the following input JSON (do not ask questions; just run the tool):\n"
            f"{t}"
        )

    # If the user typed a generic message (e.g., "give update"), don't reject it.
    # Treat it as an intent to get a yield prediction and ask for required fields.
    if not _is_supported_query(t):
        return (
            "I want a crop yield prediction. Please tell me what inputs you need and ask me for the missing required fields: "
            "State_Name, District_Name, Crop, Season, Crop_Year, Area."
        )

    return t


if __name__ == "__main__":
    agent = get_agent(verbose=False)
    prompt = _build_agent_prompt_from_user_input("")
    if prompt.startswith("The JSON you provided is not valid"):
        print(
            _as_json_response(
                {
                    "ok": False,
                    "type": "error",
                    "error": {
                        "code": "INVALID_JSON",
                        "message": prompt,
                    },
                }
            )
        )
        raise SystemExit(1)

    if not _is_supported_query(prompt):
        print(
            _as_json_response(
                {
                    "ok": False,
                    "type": "refusal",
                    "error": {
                        "code": "UNSUPPORTED_QUERY",
                        "message": "I can only help with crop yield prediction and related agriculture questions.",
                    },
                }
            )
        )
        raise SystemExit(1)

    try:
        result = agent.invoke({"messages": [("user", prompt)]})
        msgs = result.get("messages", []) if isinstance(result, dict) else []
        if msgs:
            text = _message_to_text(msgs[-1])
            parsed = _try_parse_json(text) if isinstance(text, str) else None
            if isinstance(parsed, dict):
                print(_as_json_response({"ok": True, "type": "agent_result", "data": parsed}))
            else:
                print(_as_json_response({"ok": True, "type": "agent_result", "data": {"response": text}}))
        else:
            print(_as_json_response({"ok": True, "type": "agent_result", "data": result}))
    except Exception as e:
        print(
            _as_json_response(
                {
                    "ok": False,
                    "type": "error",
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(e),
                    },
                }
            )
        )
        raise SystemExit(1)
