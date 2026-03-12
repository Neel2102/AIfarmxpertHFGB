"""
Updated Super Agent Routes - Now uses the new core agent system
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import json
import asyncio
from datetime import datetime

# Import the new core agent system
from farmxpert.core.core_agent_updated import process_farm_request
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.gemini_service import gemini_service
from farmxpert.models.database import get_db, engine
from sqlalchemy import text
from farmxpert.app.orchestrator.agent import OrchestratorAgent
from farmxpert.interfaces.api.routes.auth_routes import get_current_user
from farmxpert.models.user_models import User

logger = get_logger("super_agent_routes")

# ── DB-backed chat history helpers ─────────────────────────

def _db_get_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history for a session from DB."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT role, content FROM chat_messages WHERE session_id = :sid AND role IN ('user','assistant') ORDER BY id ASC"),
                {"sid": session_id}
            ).fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return []

def _db_save_message(session_id: str, role: str, content: str):
    """Save a single chat message to DB. Creates session if needed."""
    try:
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT id FROM chat_sessions WHERE id = :sid"), {"sid": session_id}
            ).fetchone()
            if not existing:
                title = content[:40] + "..." if len(content) > 40 else content
                conn.execute(
                    text("INSERT INTO chat_sessions (id, title) VALUES (:sid, :title)"),
                    {"sid": session_id, "title": title},
                )
            else:
                conn.execute(
                    text("UPDATE chat_sessions SET updated_at = NOW() WHERE id = :sid"),
                    {"sid": session_id},
                )
            conn.execute(
                text("INSERT INTO chat_messages (session_id, role, content) VALUES (:sid, :role, :content)"),
                {"sid": session_id, "role": role, "content": content},
            )
    except Exception as e:
        logger.error(f"Error saving message: {e}")


def _db_save_context(session_id: str, context: Dict[str, Any]) -> None:
    try:
        _db_save_message(session_id, "context", json.dumps(context))
    except Exception as e:
        logger.error(f"Error saving context: {e}")


def _db_get_context(session_id: str) -> Dict[str, Any]:
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT content FROM chat_messages WHERE session_id = :sid AND role = 'context' ORDER BY id DESC LIMIT 1"),
                {"sid": session_id},
            ).fetchone()
            if not row or not row[0]:
                return {}
            try:
                parsed = json.loads(row[0])
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
    except Exception as e:
        logger.error(f"Error reading context: {e}")
        return {}


def _db_get_farm_profile_context(user_id: Optional[int]) -> Dict[str, Any]:
    if not user_id:
        return {}
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT state, district, village, latitude, longitude, soil_type, specific_crop, primary_crops
                    FROM farm_profiles
                    WHERE user_id = :uid
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                ),
                {"uid": int(user_id)},
            ).fetchone()
            if not row:
                return {}

            state, district, village, lat, lon, soil_type, specific_crop, primary_crops = row
            ctx: Dict[str, Any] = {}
            location: Dict[str, Any] = {}
            if lat is not None and lon is not None:
                location["latitude"] = float(lat)
                location["longitude"] = float(lon)
            if state:
                location["state"] = state
            if district:
                location["district"] = district
            if village:
                location["village"] = village
            if location:
                ctx["location"] = location
            if soil_type:
                ctx["soil_type"] = soil_type
            if specific_crop:
                ctx["crop_info"] = {"name": specific_crop}
            elif primary_crops:
                ctx["primary_crops"] = primary_crops
            return ctx
    except Exception as e:
        logger.error(f"Error reading farm profile context: {e}")
        return {}


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base or {})
    for k, v in (update or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def _extract_structured_updates_from_text(message: str) -> Dict[str, Any]:
    """Very lightweight parsing to support the hybrid A+B flow.

    This only extracts obvious, explicit values (no guessing).
    """
    if not message:
        return {}
    m = message.strip()
    updates: Dict[str, Any] = {}

    import re

    # Coordinates
    lat_match = re.search(r"lat(?:itude)?\s*[:=]\s*(-?\d+\.\d+)", m, re.IGNORECASE)
    lon_match = re.search(r"lon(?:gitude)?\s*[:=]\s*(-?\d+\.\d+)", m, re.IGNORECASE)
    if lat_match and lon_match:
        updates.setdefault("location", {})
        updates["location"]["latitude"] = float(lat_match.group(1))
        updates["location"]["longitude"] = float(lon_match.group(1))

    # Area (acres)
    acres_match = re.search(r"\b(\d+(?:\.\d+)?)\s*acres?\b", m, re.IGNORECASE)
    if acres_match:
        updates["area_acres"] = float(acres_match.group(1))

    # Soil moisture percent
    sm_match = re.search(r"soil\s*moisture\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%", m, re.IGNORECASE)
    if sm_match:
        updates["soil_moisture_percent"] = float(sm_match.group(1))
    else:
        # Loose pattern: "moisture 45%"
        sm2_match = re.search(r"\bmoisture\b\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%", m, re.IGNORECASE)
        if sm2_match:
            updates["soil_moisture_percent"] = float(sm2_match.group(1))

    # Rain in last 3 days (mm)
    rain_match = re.search(r"\brain\b\s*(?:last\s*3\s*days)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*mm\b", m, re.IGNORECASE)
    if rain_match:
        updates["rain_last_3_days_mm"] = float(rain_match.group(1))
        updates.setdefault("recent_weather", {})
        updates["recent_weather"]["rain_last_3_days_mm"] = float(rain_match.group(1))

    # Simple forecast yes/no (keeps it explicit; does not invent a forecast)
    if re.search(r"\bno\s*rain\b", m, re.IGNORECASE) or re.search(r"\bdry\b", m, re.IGNORECASE):
        updates.setdefault("recent_weather", {})
        updates["recent_weather"]["forecast_next_5_days"] = ["no rain"]
    elif re.search(r"\brain\s*(?:expected|forecast)\b", m, re.IGNORECASE) or re.search(r"\brainy\b", m, re.IGNORECASE):
        updates.setdefault("recent_weather", {})
        updates["recent_weather"]["forecast_next_5_days"] = ["rain"]

    # State (very lightweight)
    state_match = re.search(r"\bstate\s*[:=]\s*([a-zA-Z ]{2,})", m, re.IGNORECASE)
    if state_match:
        updates.setdefault("location", {})
        updates["location"]["state"] = state_match.group(1).strip()

    # Freeform location: "<city> <state>" or "<city>, <state>"
    if "location" not in updates or not isinstance(updates.get("location"), dict):
        updates["location"] = {}
    if not updates["location"].get("state"):
        loc_match = re.search(r"\b([a-zA-Z]{3,})(?:\s*,\s*|\s+)([a-zA-Z]{3,})\b", m)
        if loc_match:
            city_guess = loc_match.group(1).strip()
            state_guess = loc_match.group(2).strip()
            known_states = {
                "andhra", "arunachal", "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
                "himachal", "jharkhand", "karnataka", "kerala", "madhya", "maharashtra", "manipur",
                "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
                "tamil", "telangana", "tripura", "uttar", "uttarakhand", "west", "delhi",
            }
            # Only apply if the second token looks like a state/UT keyword.
            if state_guess.lower() in known_states:
                updates["location"].setdefault("city", city_guess)
                updates["location"]["state"] = state_guess

    # pH can come as "6.5 ph" without label
    if "soil_data" not in updates:
        ph_suffix_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ph)\b", m, re.IGNORECASE)
        if ph_suffix_match:
            updates.setdefault("soil_data", {})
            updates["soil_data"]["pH"] = float(ph_suffix_match.group(1))

    # Unlabeled soil readings: "N P K pH" style numbers in a sentence.
    # If we see exactly 3 integers and one decimal, treat as N/P/K(ppm) + pH.
    nums = re.findall(r"\b\d+(?:\.\d+)?\b", m)
    if nums and len(nums) >= 4 and "soil_data" not in updates:
        try:
            floats = [float(x) for x in nums]
            decimals = [x for x in floats if not float(x).is_integer()]
            ints = [int(x) for x in floats if float(x).is_integer()]
            if len(decimals) == 1 and len(ints) >= 3:
                ph_val = float(decimals[0])
                n_val, p_val, k_val = float(ints[0]), float(ints[1]), float(ints[2])
                updates.setdefault("soil_data", {})
                updates["soil_data"].update(
                    {
                        "pH": ph_val,
                        "nitrogen": n_val,
                        "phosphorus": p_val,
                        "potassium": k_val,
                    }
                )
        except Exception:
            pass

    # Growth stage
    stage_match = re.search(r"growth\s*stage\s*[:=]\s*([a-zA-Z_ -]+)", m, re.IGNORECASE)
    if stage_match:
        updates.setdefault("crop_info", {})
        updates["crop_info"]["growth_stage"] = stage_match.group(1).strip().lower()

    # Loose growth stage keywords (explicit only)
    if "crop_info" not in updates or "growth_stage" not in updates.get("crop_info", {}):
        for stage_kw in ["sowing", "vegetative", "flowering", "fruiting", "tillering", "harvest", "nursery"]:
            if re.search(rf"\b{re.escape(stage_kw)}\b", m, re.IGNORECASE):
                updates.setdefault("crop_info", {})
                updates["crop_info"]["growth_stage"] = stage_kw
                break

    # Mirror crop_info.growth_stage to root growth_stage (used by irrigation/fertilizer/soil agents)
    if isinstance(updates.get("crop_info"), dict) and updates["crop_info"].get("growth_stage"):
        updates["growth_stage"] = updates["crop_info"]["growth_stage"]

    # Crop name
    crop_match = re.search(r"crop\s*[:=]\s*([a-zA-Z_ -]+)", m, re.IGNORECASE)
    if crop_match:
        updates.setdefault("crop_info", {})
        updates["crop_info"]["name"] = crop_match.group(1).strip().lower()

    # Mirror crop_info.name to root crop (string) for agents expecting crop
    if isinstance(updates.get("crop_info"), dict) and updates["crop_info"].get("name"):
        updates["crop"] = updates["crop_info"]["name"]

    # Soil test values (ppm / EC)
    ph_match = re.search(r"\bpH\b\s*[:=]\s*(\d+(?:\.\d+)?)", m)
    n_match = re.search(r"\bN(?:itrogen)?\b\s*[:=]\s*(\d+(?:\.\d+)?)", m, re.IGNORECASE)
    p_match = re.search(r"\bP(?:hosphorus)?\b\s*[:=]\s*(\d+(?:\.\d+)?)", m, re.IGNORECASE)
    k_match = re.search(r"\bK(?:otassium)?\b\s*[:=]\s*(\d+(?:\.\d+)?)", m, re.IGNORECASE)
    ec_match = re.search(r"\bEC\b\s*[:=]\s*(\d+(?:\.\d+)?)", m, re.IGNORECASE)
    if any([ph_match, n_match, p_match, k_match, ec_match]):
        updates.setdefault("soil_data", {})
        if ph_match:
            updates["soil_data"]["pH"] = float(ph_match.group(1))
        if n_match:
            updates["soil_data"]["nitrogen"] = float(n_match.group(1))
        if p_match:
            updates["soil_data"]["phosphorus"] = float(p_match.group(1))
        if k_match:
            updates["soil_data"]["potassium"] = float(k_match.group(1))
        if ec_match:
            updates["soil_data"]["electrical_conductivity"] = float(ec_match.group(1))

    return updates

def _db_get_all_sessions() -> List[Dict[str, Any]]:
    """Get all chat sessions for the sidebar."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT s.id, s.title, s.updated_at, COUNT(m.id) as msg_count
                    FROM chat_sessions s
                    LEFT JOIN chat_messages m ON m.session_id = s.id
                    GROUP BY s.id, s.title, s.updated_at
                    ORDER BY s.updated_at DESC
                    LIMIT 50
                """)
            ).fetchall()
            return [
                {
                    "session_id": r[0],
                    "title": r[1],
                    "message_count": r[3],
                    "updated_at": r[2].isoformat() if r[2] else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return []

# Keep in-memory fallback for current-session context window
CHAT_HISTORY_STORE: Dict[str, List[Dict[str, str]]] = {}

def _safe_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))

def _find_first_key(data: Any, keys: List[str]) -> Optional[Any]:
    if not isinstance(data, dict):
        return None
    for k in keys:
        if k in data and _safe_scalar(data[k]):
            return data[k]
    for v in data.values():
        if isinstance(v, dict):
            found = _find_first_key(v, keys)
            if found is not None:
                return found
    return None

def _dict_to_rows(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for k, v in d.items():
        if _safe_scalar(v):
            rows.append({"field": str(k), "value": v})
    return rows

def _build_agent_ui_item(agent_name: str, success: bool, data: Any, error: Optional[str]) -> Dict[str, Any]:
    status = "success" if success else "error"

    summary_parts: List[str] = []
    temperature = _find_first_key(data, ["temperature", "temp", "temperature_c", "temperature_celsius"])
    humidity = _find_first_key(data, ["humidity", "humidity_percent", "humidity_pct"])
    condition = _find_first_key(data, ["weather_condition", "condition", "weather", "weather_type"])
    if temperature is not None:
        summary_parts.append(f"Temperature: {temperature}")
    if condition is not None and isinstance(condition, str):
        summary_parts.append(str(condition))

    summary = ", ".join(summary_parts) if summary_parts else (str(error) if error else "")

    metrics: List[Dict[str, Any]] = []
    if humidity is not None:
        metrics.append({"label": "Humidity", "value": humidity, "unit": "%", "emphasis": True})
    wind_speed = _find_first_key(data, ["wind_speed", "wind", "windSpeed"])
    if wind_speed is not None:
        metrics.append({"label": "Wind Speed", "value": wind_speed, "unit": "m/s"})
    rainfall = _find_first_key(data, ["rainfall_mm", "rainfall", "precipitation_mm", "precipitation"])
    if rainfall is not None:
        metrics.append({"label": "Rainfall", "value": rainfall, "unit": "mm"})

    groups: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                rows = _dict_to_rows(v)
                if rows:
                    groups.append({"groupTitle": str(k), "rows": rows})

        root_rows = []
        for k, v in data.items():
            if isinstance(v, dict):
                continue
            if _safe_scalar(v) and k not in {"recommendations", "warnings"}:
                root_rows.append({"field": str(k), "value": v})
        if root_rows:
            groups.insert(0, {"groupTitle": "data", "rows": root_rows})

    widgets: List[Dict[str, Any]] = []
    if metrics:
        widgets.append({"type": "metric_grid", "columns": 2, "items": metrics})
    if groups:
        widgets.append({"type": "table_grouped", "title": "Detailed Data", "groups": groups})
    if not success and error:
        widgets.append({
            "type": "alert",
            "variant": "error",
            "title": "Agent Failed",
            "message": str(error)
        })

    return {
        "agent": {
            "id": agent_name,
            "name": agent_name.replace("_", " ").title(),
            "status": status,
            "statusBadge": "Success" if success else "Failed"
        },
        "summary": summary,
        "widgets": widgets
    }

def _build_smart_chat_ui(answer_text: str, agent_name: str, success: bool, data: Any, error: Optional[str]) -> Dict[str, Any]:
    item = _build_agent_ui_item(agent_name=agent_name, success=success, data=data, error=error)
    return {
        "type": "smart_chat_ui_v1",
        "state": {"phase": "completed", "loading": False},
        "header": {
            "title": "Agent Results (1)",
            "subtitle": answer_text or "Response ready."
        },
        "sections": [
            {
                "type": "agent_results",
                "collapsible": True,
                "defaultCollapsed": False,
                "items": [item]
            }
        ]
    }

# ── Request/Response Models ─────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    user_id: Optional[int] = Field(None, description="User ID")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _orchestrator_results_to_agent_responses(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    agent_responses: List[Dict[str, Any]] = []
    if not isinstance(results, dict):
        return agent_responses

    for agent_name, raw in results.items():
        if isinstance(raw, dict):
            success = bool(raw.get("success")) and not raw.get("error")
            error = raw.get("error")
            data = raw.get("data") if "data" in raw else raw
        else:
            success = False
            error = "Invalid agent response"
            data = raw

        quality = "live"
        agent_name_norm = str(agent_name).strip().lower()
        if agent_name_norm == "growth_stage_monitor":
            quality = "mock"
        if agent_name_norm == "task_scheduler_agent" and isinstance(data, dict):
            tasks = data.get("tasks_for_today")
            if isinstance(tasks, list) and any((t.get("task") == "Inspect crop health in Field A") for t in tasks if isinstance(t, dict)):
                quality = "fallback"

        agent_responses.append(
            {
                "agent_name": str(agent_name),
                "success": success,
                "data": data,
                "error": error,
                "quality": quality,
            }
        )

    return agent_responses


def _tools_used_from_agents(agents_used: Any) -> List[str]:
    if not agents_used:
        return []

    agents: List[str] = []
    if isinstance(agents_used, list):
        agents = [str(a) for a in agents_used if a]
    else:
        agents = [str(agents_used)]

    # Normalize orchestrator agent names into tool keys expected by frontend cards.
    tools: List[str] = []
    for a in agents:
        a_norm = a.strip().lower()
        if a_norm in {"weather_watcher", "weather"}:
            tools.append("weather")
        elif a_norm in {"market_intelligence_agent", "market_intelligence", "market"}:
            tools.append("market")
        elif a_norm in {"soil_health_agent", "soil"}:
            tools.append("soil")
        elif a_norm in {"fertilizer_agent", "fertilizer"}:
            tools.append("fertilizer")
        elif a_norm in {"irrigation_agent", "irrigation"}:
            tools.append("irrigation")
        elif a_norm in {"growth_stage_monitor", "crop"}:
            tools.append("crop")
        elif a_norm in {"task_scheduler_agent", "task_scheduler", "task"}:
            tools.append("task")

    # De-duplicate while preserving order
    deduped: List[str] = []
    for t in tools:
        if t not in deduped:
            deduped.append(t)
    return deduped


def _extract_missing_inputs(agent_responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    missing: List[Dict[str, Any]] = []
    for r in agent_responses or []:
        if not isinstance(r, dict):
            continue
        data = r.get("data")
        if isinstance(data, dict) and data.get("error") == "Missing required inputs":
            missing.append(
                {
                    "agent": data.get("agent") or r.get("agent_name"),
                    "missing_fields": data.get("missing_fields") or [],
                    "questions": data.get("questions") or [],
                }
            )
    return missing

# ── Router ─────────────────────────

router = APIRouter(prefix="/super-agent", tags=["super-agent"])

@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint using the new core agent system
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Save user message
        _db_save_message(session_id, "user", request.message)
        
        # Use farmer_coach as default agent for general chat
        # The core agent will determine the best role
        response = await process_farm_request(
            user_input=request.message,
            agent_role="farmer_coach",  # Default role, can be overridden by core agent logic
            context=request.context or {},
            session_id=session_id,
            user_id=request.user_id
        )
        
        # Extract response text
        response_text = response.get("response", "I'm sorry, I couldn't process that request.")
        
        # Save assistant response
        _db_save_message(session_id, "assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used=response.get("agent"),
            metadata=response.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/orchestrated-chat")
async def orchestrated_chat(request: ChatRequest) -> Dict[str, Any]:
    """Multi-agent SuperAgent chat using OrchestratorAgent (weather/market/soil/etc.)."""
    try:
        start_time = datetime.utcnow()
        session_id = request.session_id or str(uuid.uuid4())

        _db_save_message(session_id, "user", request.message)

        existing_context = _db_get_context(session_id)
        profile_context = _db_get_farm_profile_context(request.user_id)
        message_updates = _extract_structured_updates_from_text(request.message)
        merged_context = _deep_merge(existing_context, profile_context)
        if isinstance(request.context, dict):
            merged_context = _deep_merge(merged_context, request.context)
        merged_context = _deep_merge(merged_context, message_updates)
        _db_save_context(session_id, merged_context)

        orchestrator_request: Dict[str, Any] = {"query": request.message}
        orchestrator_request.update(merged_context)

        # Default to multi-agent routing for SuperAgent unless caller provided a strategy.
        orchestrator_request.setdefault("strategy", "comprehensive_analysis")

        orchestrator_result = await OrchestratorAgent.handle_request(orchestrator_request)

        success = bool(orchestrator_result.get("success")) and not orchestrator_result.get("error")
        agents_used = orchestrator_result.get("agents_used") or []
        results = orchestrator_result.get("results") or {}

        agent_responses = _orchestrator_results_to_agent_responses(results)
        missing_inputs = _extract_missing_inputs(agent_responses)
        if missing_inputs:
            questions: List[str] = []
            for m in missing_inputs:
                for q in (m.get("questions") or []):
                    if isinstance(q, str) and q not in questions:
                        questions.append(q)

            response_text = "I need a few details to answer accurately:\n" + "\n".join(f"- {q}" for q in questions)
            _db_save_message(session_id, "assistant", response_text)

            tools_used = _tools_used_from_agents(agents_used)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return {
                "success": False,
                "agent": "super_agent_orchestrator",
                "response": response_text,
                "session_id": session_id,
                "agent_responses": agent_responses,
                "metadata": {
                    "execution_time": execution_time,
                    "tools_used": tools_used,
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_type": orchestrator_result.get("query_type"),
                    "missing_inputs": missing_inputs,
                },
                "data": {
                    "routing": orchestrator_result.get("routing"),
                    "results": results,
                    "formatted_results": orchestrator_result.get("formatted_results"),
                    "agents_used": agents_used,
                },
            }

        # Build a detailed, user-focused answer by synthesizing orchestrator outputs
        # through the core agent (instead of the orchestrator's brief summary).
        synthesis_context: Dict[str, Any] = {
            "orchestrator": {
                "query_type": orchestrator_result.get("query_type"),
                "agents_used": agents_used,
                "results": results,
                "formatted_results": orchestrator_result.get("formatted_results"),
                "recommendations": orchestrator_result.get("recommendations"),
            }
        }

        synthesis: Dict[str, Any] = {}
        response_text = ""
        last_err: Optional[str] = None
        for attempt in range(3):
            try:
                synthesis = await process_farm_request(
                    user_input=request.message,
                    agent_role="farmer_coach",
                    context=synthesis_context,
                    session_id=session_id,
                    user_id=request.user_id,
                )
                response_text = synthesis.get("response") or ""
                if response_text:
                    rt_lower = response_text.lower()
                    is_busy_text = ("busy" in rt_lower) or ("high demand" in rt_lower) or ("rate limit" in rt_lower) or ("429" in rt_lower)
                    if is_busy_text:
                        last_err = response_text
                        if attempt < 2:
                            await asyncio.sleep(0.8 * (attempt + 1))
                            response_text = ""
                            continue
                    break
            except Exception as e:
                last_err = str(e)
                err_lower = last_err.lower()
                is_busy = ("busy" in err_lower) or ("high demand" in err_lower) or ("rate limit" in err_lower) or ("429" in err_lower)
                if attempt < 2 and is_busy:
                    await asyncio.sleep(0.8 * (attempt + 1))
                    continue
                break

        if not response_text:
            fallback = orchestrator_result.get("llm_summary")
            if isinstance(fallback, str) and fallback.strip():
                response_text = fallback.strip()
            else:
                # Avoid returning the busy message as the final answer if possible.
                if last_err and ("busy" in last_err.lower() or "high demand" in last_err.lower()):
                    response_text = "I couldn't generate the final answer right now due to high demand. Please try again in a few seconds."
                else:
                    response_text = last_err or "I couldn't generate a detailed response right now."

        _db_save_message(session_id, "assistant", response_text)
        tools_used = _tools_used_from_agents(agents_used)
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return {
            "success": success,
            "agent": "super_agent_orchestrator",
            "response": response_text,
            "session_id": session_id,
            "agent_responses": agent_responses,
            "metadata": {
                "execution_time": execution_time,
                "tools_used": tools_used,
                "timestamp": datetime.utcnow().isoformat(),
                "query_type": orchestrator_result.get("query_type"),
                "data_quality": {
                    "note": "Some sub-agents may return fallback/mock outputs depending on configuration.",
                    "agent_quality": {a.get("agent_name"): a.get("quality") for a in agent_responses if isinstance(a, dict)},
                },
            },
            "data": {
                "routing": orchestrator_result.get("routing"),
                "results": results,
                "formatted_results": orchestrator_result.get("formatted_results"),
                "agents_used": agents_used,
            },
        }

    except Exception as e:
        logger.error(f"Orchestrated chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orchestrated chat failed: {str(e)}")

@router.post("/agent-chat")
async def agent_chat(
    message: str,
    agent_role: str = "farmer_coach",
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Chat with a specific agent role
    """
    try:
        # Generate session ID if not provided
        session_id = session_id or str(uuid.uuid4())
        
        # Save user message
        _db_save_message(session_id, "user", message)
        
        # Call the core agent with specific role
        response = await process_farm_request(
            user_input=message,
            agent_role=agent_role,
            context=context or {},
            session_id=session_id,
            user_id=user_id
        )
        
        # Extract response text
        response_text = response.get("response", "I'm sorry, I couldn't process that request.")
        
        # Save assistant response
        _db_save_message(session_id, "assistant", response_text)
        
        # Build UI response for compatibility
        ui = _build_smart_chat_ui(
            answer_text=response_text,
            agent_name=agent_role,
            success=response.get("success", True),
            data=response.get("data", {}),
            error=response.get("error") if not response.get("success") else None
        )
        
        return {
            "response": response_text,
            "session_id": session_id,
            "agent": agent_role,
            "success": response.get("success", True),
            "ui": ui,
            "metadata": response.get("metadata")
        }
        
    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")

@router.get("/sessions")
async def get_sessions() -> List[Dict[str, Any]]:
    """Get all chat sessions"""
    return _db_get_all_sessions()


@router.get("/history")
async def get_history(session_id: Optional[str] = None) -> Any:
    if session_id:
        return _db_get_history(session_id)
    return _db_get_all_sessions()

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history for a specific session"""
    return _db_get_history(session_id)

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """Delete a chat session"""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM chat_messages WHERE session_id = :sid"),
                {"sid": session_id}
            )
            conn.execute(
                text("DELETE FROM chat_sessions WHERE id = :sid"),
                {"sid": session_id}
            )
            conn.commit()
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for super agent system"""
    try:
        # Test the core agent system
        from farmxpert.core.core_agent_updated import core_agent
        
        available_agents = core_agent.get_available_agents()
        
        return {
            "status": "healthy",
            "core_agent": "active",
            "available_agents": len(available_agents),
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def delete_session(session_id: str, user_id: int) -> bool:
    """Delete a chat session and its messages, ensuring it belongs to the user."""
    with engine.connect() as conn:
        # First delete messages for this session (only if belongs to user)
        del_msg = conn.execute(
            text("DELETE FROM chat_messages WHERE session_id = :sid AND session_id IN (SELECT id FROM chat_sessions WHERE user_id = :uid)"),
            {"sid": session_id, "uid": user_id}
        )
        # Then delete the session (only if belongs to user)
        del_sess = conn.execute(
            text("DELETE FROM chat_sessions WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": user_id}
        )
        conn.commit()
        # If session was not found for this user, return False
        return del_sess.rowcount > 0


@router.delete("/history/{session_id}")
async def delete_session_history(session_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a specific chat session and all its messages for the authenticated user.
    """
    try:
        # Delete session from DB (only if it belongs to the current user)
        success = delete_session(session_id=session_id, user_id=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        # Also clear from in-memory cache if exists
        CHAT_HISTORY_STORE.pop(session_id, None)
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
