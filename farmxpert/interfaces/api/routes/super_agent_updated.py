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

logger = get_logger("super_agent_routes")

# ── DB-backed chat history helpers ─────────────────────────

def _db_get_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history for a session from DB."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT role, content FROM chat_messages WHERE session_id = :sid ORDER BY id ASC"),
                {"sid": session_id}
            ).fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return []

def _db_save_message(session_id: str, role: str, content: str):
    """Save a single chat message to DB. Creates session if needed."""
    try:
        with engine.connect() as conn:
            # Ensure session exists
            existing = conn.execute(
                text("SELECT id FROM chat_sessions WHERE id = :sid"), {"sid": session_id}
            ).fetchone()
            if not existing:
                title = content[:40] + "..." if len(content) > 40 else content
                conn.execute(
                    text("INSERT INTO chat_sessions (id, title) VALUES (:sid, :title)"),
                    {"sid": session_id, "title": title}
                )
            else:
                conn.execute(
                    text("UPDATE chat_sessions SET updated_at = NOW() WHERE id = :sid"),
                    {"sid": session_id}
                )
            conn.execute(
                text("INSERT INTO chat_messages (session_id, role, content) VALUES (:sid, :role, :content)"),
                {"sid": session_id, "role": role, "content": content}
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving message: {e}")

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
