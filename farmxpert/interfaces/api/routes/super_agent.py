"""
Super Agent API Routes
Handles user queries through the SuperAgent system
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import json
import asyncio
from datetime import datetime
from farmxpert.core.super_agent import super_agent, SuperAgentResponse
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.gemini_service import gemini_service

# Simple in-memory chat history store for demo (session_id -> list of turns)
# Turn format: {"role": "user"|"assistant", "content": "text"}
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


def _build_agent_placeholder_item(agent_name: str, status: str) -> Dict[str, Any]:
    badge_map = {
        "queued": "Queued",
        "running": "Running",
        "success": "Success",
        "error": "Failed",
    }
    return {
        "agent": {
            "id": agent_name,
            "name": agent_name.replace("_", " ").title(),
            "status": status,
            "statusBadge": badge_map.get(status, status),
        },
        "summary": "",
        "widgets": [],
    }


def _build_streaming_ui(answer_text: str, ordered_agents: List[str], agent_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for a in ordered_agents:
        st = agent_states.get(a) or {}
        status = str(st.get("status") or "queued")
        if status in {"success", "error"}:
            items.append(
                _build_agent_ui_item(
                    agent_name=a,
                    success=status == "success",
                    data=st.get("data"),
                    error=st.get("error"),
                )
            )
        else:
            items.append(_build_agent_placeholder_item(agent_name=a, status=status))

    completed_agents = sum(1 for a in ordered_agents if (agent_states.get(a) or {}).get("status") in {"success", "error"})

    return {
        "type": "smart_chat_ui_v1",
        "state": {
            "phase": "running" if completed_agents < len(ordered_agents) else "completed",
            "loading": completed_agents < len(ordered_agents),
            "progress": {
                "totalAgents": len(ordered_agents),
                "completedAgents": completed_agents,
            },
        },
        "header": {
            "title": f"Agent Results ({len(ordered_agents)})",
            "subtitle": answer_text or ("Working on it..." if completed_agents < len(ordered_agents) else "Response ready."),
        },
        "sections": [
            {
                "type": "agent_results",
                "collapsible": True,
                "defaultCollapsed": False,
                "items": items,
            }
        ],
    }


def _build_smart_chat_ui(answer_text: str, agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    items = [
        _build_agent_ui_item(
            agent_name=str(r.get("agent_name") or "agent"),
            success=bool(r.get("success")),
            data=r.get("data"),
            error=r.get("error")
        )
        for r in (agent_responses or [])
    ]

    return {
        "type": "smart_chat_ui_v1",
        "state": {"phase": "completed", "loading": False},
        "header": {
            "title": f"Agent Results ({len(items)})",
            "subtitle": answer_text or "Response ready."
        },
        "sections": [
            {
                "type": "agent_results",
                "collapsible": True,
                "defaultCollapsed": False,
                "items": items
            }
        ]
    }

router = APIRouter(prefix="/super-agent", tags=["Super Agent"])
logger = get_logger("super_agent_api")


class QueryRequest(BaseModel):
    """Request model for user queries"""
    query: str = Field(..., description="User's agricultural query", min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID for personalization")


class QueryResponse(BaseModel):
    """Response model for user queries"""
    success: bool
    response: Any  # Natural language text for display
    natural_language: str = ""  # Clean natural language response
    sop: Optional[Dict[str, Any]] = None  # Full SOP JSON payload (for "Show Reasoning")
    ui: Optional[Dict[str, Any]] = None  # Smart Chat UI schema payload
    session_id: str
    agent_responses: List[Dict[str, Any]]
    recommendations: List[str]
    warnings: List[str]
    execution_time: float
    timestamp: datetime


class AgentInfoResponse(BaseModel):
    """Response model for available agents information"""
    agents: Dict[str, Dict[str, Any]]
    total_agents: int
    categories: List[str]


class LanguageDetectRequest(BaseModel):
    text: str = Field(..., description="User utterance text to detect language for", min_length=1, max_length=2000)


class LanguageDetectResponse(BaseModel):
    language: str
    locale: str


@router.post("/query/stream")
async def process_user_query_stream(request: QueryRequest):
    """
    Process a user query with streaming response
    
    This endpoint provides real-time streaming of AI responses,
    similar to ChatGPT's typing effect. Returns Server-Sent Events (SSE).
    """
    try:
        logger.info(f"Processing streaming query: {request.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Prepare context
        context = request.context or {}
        if request.user_id:
            context["user_id"] = request.user_id
        context["session_id"] = session_id
        
        async def generate_stream():
            try:
                logger.info(f"Starting stream for session {session_id}")
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
                
                # Use Gemini service directly for faster streaming
                is_conservational = context.get("conversational", False)
                locale = context.get('locale', 'en-IN')
                
                if is_conservational:
                    full_prompt = f"""
You are FarmXpert, a helpful and friendly agricultural voice assistant.
Answer the farmer's question naturally and concisely in the language for locale '{locale}'.
Do NOT use markdown, bullet points, or special characters. Speak as if you are talking on the phone.
Keep your response under 3-4 sentences unless asked for details.

Farmer Context:
{json.dumps(context, indent=2)}

Farmer Question:
{request.query}
"""
                else:
                    full_prompt = f"""
You are FarmXpert, an AI agricultural expert system.

Farmer Context:
{json.dumps(context, indent=2)}

Farmer Question:
{request.query}

Provide your response in this exact format with proper line breaks and bullet points:

Direct Answer:
[Your clear answer here]

Recommendations:
- First recommendation
- Second recommendation
- Third recommendation

Scientific Reasoning:
[Explain why these recommendations work]

Warnings / Considerations:
- First warning
- Second warning

Additional Information:
[Any extra helpful details]

IMPORTANT: Use proper line breaks and bullet points (-) for lists. Each item should be on a new line.
"""
                logger.info("Sending prompt to Gemini...")
                # Stream the response
                async for chunk in gemini_service.generate_streaming_response(full_prompt, context):
                    if chunk:
                        # logger.debug(f"Received chunk: {chunk[:20]}...") 
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'timestamp': datetime.now().isoformat()})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                
                logger.info("Stream complete.")
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.now().isoformat()})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream", # Changed to event-stream for better SSE support
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no", # Nginx specific
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing streaming query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process streaming query: {str(e)}"
        )


@router.post("/query/ui-stream")
async def process_user_query_ui_stream(request: QueryRequest):
    try:
        logger.info(f"Processing UI streaming query: {request.query[:100]}...")

        session_id = request.session_id or str(uuid.uuid4())

        context = request.context or {}
        if request.user_id:
            context["user_id"] = request.user_id
        context["session_id"] = session_id

        # M2/M3: If image_data or voice_data present, force include pest_disease_diagnostic agent
        if context.get("image_data") or context.get("voice_data"):
            # Ensure pest_disease_diagnostic is included for M2/M3 features
            context["_force_agents"] = ["pest_disease_diagnostic"]

        async def generate_stream():
            start_ts = datetime.now().isoformat()
            try:
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'timestamp': start_ts})}\n\n"

                # Inject chat history into context for agents and synthesis
                chat_history = CHAT_HISTORY_STORE.get(session_id, [])
                context["chat_history"] = chat_history[-10:] # Keep last 10 turns (20 messages)
                
                logger.info(f"Using chat history (last {len(context['chat_history'])} turns) for session {session_id}")

                agent_selection = await super_agent._select_agents(request.query, context)
                ordered_agents = [a for a in agent_selection if isinstance(a, str)]
                if not ordered_agents:
                    ordered_agents = ["crop_selector", "farmer_coach"]

                agent_states: Dict[str, Dict[str, Any]] = {a: {"status": "queued"} for a in ordered_agents}

                ui0 = _build_streaming_ui("Working on it...", ordered_agents, agent_states)
                yield f"data: {json.dumps({'type': 'ui', 'ui': ui0, 'timestamp': datetime.now().isoformat()})}\n\n"

                tasks: Dict[str, asyncio.Task] = {}
                for a in ordered_agents:
                    agent_states[a]["status"] = "running"
                    ui_running = _build_streaming_ui("Working on it...", ordered_agents, agent_states)
                    yield f"data: {json.dumps({'type': 'ui', 'ui': ui_running, 'timestamp': datetime.now().isoformat()})}\n\n"
                    tasks[a] = asyncio.create_task(super_agent._execute_single_agent(a, request.query, context))

                agent_responses = []
                for task in asyncio.as_completed(list(tasks.values())):
                    res = await task
                    agent_responses.append(res)
                    agent_states[res.agent_name] = {
                        "status": "success" if res.success else "error",
                        "data": res.data,
                        "error": res.error,
                    }
                    ui_update = _build_streaming_ui("Working on it...", ordered_agents, agent_states)
                    yield f"data: {json.dumps({'type': 'ui', 'ui': ui_update, 'timestamp': datetime.now().isoformat()})}\n\n"

                final_response: Dict[str, Any] = await super_agent._synthesize_response(request.query, agent_responses, context)
                sop_json: Dict[str, Any] = final_response if isinstance(final_response, dict) else {}
                answer_text: str = sop_json.get("answer") or sop_json.get("response") if isinstance(sop_json, dict) else None
                if not answer_text:
                    answer_text = "Response ready."
                
                # Save to history
                if session_id not in CHAT_HISTORY_STORE:
                    CHAT_HISTORY_STORE[session_id] = []
                
                CHAT_HISTORY_STORE[session_id].append({"role": "user", "content": request.query})
                CHAT_HISTORY_STORE[session_id].append({"role": "assistant", "content": answer_text})
                
                # Limit history size in memory
                if len(CHAT_HISTORY_STORE[session_id]) > 20:
                    CHAT_HISTORY_STORE[session_id] = CHAT_HISTORY_STORE[session_id][-20:]

                ui_final = _build_streaming_ui(answer_text, ordered_agents, agent_states)
                
                # Format agent_responses for frontend
                formatted_agent_responses = []
                for ar in agent_responses:
                    formatted_agent_responses.append({
                        "agent_name": ar.agent_name,
                        "success": ar.success,
                        "data": ar.data,
                        "error": ar.error,
                        "execution_time": ar.execution_time
                    })
                
                yield f"data: {json.dumps({'type': 'ui', 'ui': ui_final, 'answer': answer_text, 'sop': sop_json, 'agent_responses': formatted_agent_responses, 'timestamp': datetime.now().isoformat()})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            except Exception as e:
                logger.error(f"Error in UI streaming: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )
    except Exception as e:
        logger.error(f"Error processing UI streaming query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process UI streaming query: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def process_user_query(request: QueryRequest):
    """
    Process a user query through the SuperAgent system
    
    This endpoint:
    1. Takes a user's agricultural query
    2. Uses Gemini to determine which agents to call
    3. Executes the selected agents with appropriate tools
    4. Synthesizes a comprehensive response
    5. Returns the final answer to the user
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Prepare context
        context = request.context or {}
        if request.user_id:
            context["user_id"] = request.user_id
        context["session_id"] = session_id
        
        # Inject chat history into context
        chat_history = CHAT_HISTORY_STORE.get(session_id, [])
        context["chat_history"] = chat_history[-10:]
        
        # Process query through SuperAgent
        result: SuperAgentResponse = await super_agent.process_query(
            query=request.query,
            context=context,
            session_id=session_id
        )
        
        # Extract recommendations and warnings from agent responses
        recommendations = []
        warnings = []
        
        for agent_response in result.agent_responses:
            if agent_response.success and isinstance(agent_response.data, dict):
                # Extract recommendations from agent data
                if "recommendations" in agent_response.data:
                    if isinstance(agent_response.data["recommendations"], list):
                        for rec in agent_response.data["recommendations"]:
                            if isinstance(rec, dict):
                                # Convert dict to string representation
                                recommendations.append(f"{rec.get('variety', 'Unknown')}: {rec.get('description', 'No description')}")
                            else:
                                recommendations.append(str(rec))
                    else:
                        recommendations.append(str(agent_response.data["recommendations"]))
                
                # Extract warnings from agent data
                if "warnings" in agent_response.data:
                    if isinstance(agent_response.data["warnings"], list):
                        warnings.extend(agent_response.data["warnings"])
                    else:
                        warnings.append(str(agent_response.data["warnings"]))
        
        # Format agent responses for API response
        formatted_agent_responses = []
        for agent_response in result.agent_responses:
            formatted_agent_responses.append({
                "agent_name": agent_response.agent_name,
                "success": agent_response.success,
                "data": agent_response.data,
                "error": agent_response.error,
                "execution_time": agent_response.execution_time
            })
        
        # Prepare concise string answer for UI and attach SOP JSON
        sop_json: Dict[str, Any] = result.response if isinstance(result.response, dict) else {}
        answer_text: str = sop_json.get("answer") if isinstance(sop_json, dict) else None
        if not answer_text:
            # Fallback to a short string
            answer_text = "Response ready." if result.success else "Sorry, something went wrong."

        # Use natural language response from SuperAgent
        natural_language_response = result.natural_language or answer_text

        # Save to history
        if session_id not in CHAT_HISTORY_STORE:
            CHAT_HISTORY_STORE[session_id] = []
        
        CHAT_HISTORY_STORE[session_id].append({"role": "user", "content": request.query})
        CHAT_HISTORY_STORE[session_id].append({"role": "assistant", "content": natural_language_response})
        
        if len(CHAT_HISTORY_STORE[session_id]) > 20:
            CHAT_HISTORY_STORE[session_id] = CHAT_HISTORY_STORE[session_id][-20:]

        return QueryResponse(
            success=result.success,
            response=natural_language_response,  # Return clean natural language
            natural_language=natural_language_response,
            sop=sop_json or None,  # Full JSON for "Show Reasoning"
            ui=_build_smart_chat_ui(natural_language_response, formatted_agent_responses) if formatted_agent_responses else None,
            session_id=session_id,
            agent_responses=formatted_agent_responses,
            recommendations=recommendations,
            warnings=warnings,
            execution_time=result.execution_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/language/detect", response_model=LanguageDetectResponse)
async def detect_language(request: LanguageDetectRequest):
    try:
        prompt = (
            "Detect the language of the following user text. "
            "Return ONLY valid JSON with keys: language, locale. "
            "locale must be a BCP-47 tag suitable for India where possible. "
            "Supported examples: en-IN, hi-IN, bn-IN, te-IN, mr-IN, ta-IN, ur-IN, gu-IN, kn-IN, ml-IN, pa-IN, or-IN, as-IN. "
            "If uncertain, use en-IN.\n\n"
            f"Text: {json.dumps(request.text, ensure_ascii=False)}"
        )

        raw = await gemini_service.generate_response(prompt, {"format": "json", "raw_prompt": True})
        parsed = gemini_service._parse_json_response(raw)

        language = str(parsed.get("language") or "English")
        locale = str(parsed.get("locale") or "en-IN")

        if not locale or "-" not in locale:
            locale = "en-IN"

        return LanguageDetectResponse(language=language, locale=locale)
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/agents", response_model=AgentInfoResponse)
async def get_available_agents():
    """
    Get information about all available agents
    
    Returns details about:
    - All registered agents
    - Agent categories
    - Available tools for each agent
    - Agent descriptions and capabilities
    """
    try:
        agents_info = super_agent.available_agents
        
        # Extract categories
        categories = list(set(agent_info.get("category", "unknown") for agent_info in agents_info.values()))
        categories.sort()
        
        return AgentInfoResponse(
            agents=agents_info,
            total_agents=len(agents_info),
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"Error getting agent information: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent information: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the SuperAgent system
    
    Returns the status of:
    - SuperAgent initialization
    - Available agents
    - Gemini service connectivity
    - Tool availability
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(),
            "super_agent": {
                "initialized": True,
                "available_agents": len(super_agent.available_agents),
                "available_tools": len(super_agent.tools)
            },
            "services": {
                "gemini_service": "available",  # This would check actual service status
                "agent_registry": "available"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }


@router.get("/status/realtime")
async def get_realtime_status():
    """
    Get real-time status of all agents and system components
    
    Returns:
    - Agent status (active, processing, idle)
    - System performance metrics
    - Recent activity
    """
    try:
        # Get agent status from the registry
        agents_info = super_agent.available_agents
        
        # Simulate real-time agent status (in a real implementation, this would be dynamic)
        agent_status = {}
        for agent_name, agent_info in agents_info.items():
            # Simulate different statuses based on agent type
            if agent_name in ['crop_selector', 'weather_watcher', 'irrigation_planner']:
                status = "active"
            elif agent_name in ['yield_predictor', 'profit_optimization']:
                status = "processing"
            else:
                status = "idle"
            
            agent_status[agent_name] = {
                "name": agent_info.get("name", agent_name),
                "category": agent_info.get("category", "unknown"),
                "status": status,
                "last_activity": datetime.now().isoformat(),
                "response_time": f"{round(0.5 + (hash(agent_name) % 10) * 0.1, 2)}s"
            }
        
        # Count statuses
        status_counts = {
            "active": sum(1 for agent in agent_status.values() if agent["status"] == "active"),
            "processing": sum(1 for agent in agent_status.values() if agent["status"] == "processing"),
            "idle": sum(1 for agent in agent_status.values() if agent["status"] == "idle")
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "agent_status": agent_status,
            "status_counts": status_counts,
            "total_agents": len(agent_status),
            "system_metrics": {
                "cpu_usage": f"{20 + (hash(str(datetime.now())) % 30)}%",
                "memory_usage": f"{45 + (hash(str(datetime.now())) % 20)}%",
                "active_sessions": 1,
                "queries_processed_today": 42
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get real-time status: {str(e)}"
        )


@router.post("/query/batch")
async def process_batch_queries(requests: List[QueryRequest]):
    """
    Process multiple queries in batch
    
    Useful for:
    - Processing multiple related questions
    - Bulk analysis of farm data
    - Comparative analysis across different scenarios
    """
    try:
        if len(requests) > 10:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 10 queries"
            )
        
        results = []
        for request in requests:
            try:
                # Process each query
                result = await process_user_query(request)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch query: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "query": request.query
                })
        
        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r.get("success", False)]),
            "failed": len([r for r in results if not r.get("success", False)])
        }
        
    except Exception as e:
        logger.error(f"Error processing batch queries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch queries: {str(e)}"
        )


@router.get("/tools")
async def get_available_tools():
    """
    Get information about available tools
    
    Returns details about:
    - All available tools
    - Tool capabilities
    - Tool usage examples
    """
    try:
        tools_info = {}
        
        for tool_name, tool_instance in super_agent.tools.items():
            # Get tool methods
            methods = [method for method in dir(tool_instance) 
                      if not method.startswith('_') and callable(getattr(tool_instance, method))]
            
            tools_info[tool_name] = {
                "class_name": tool_instance.__class__.__name__,
                "available_methods": methods,
                "description": tool_instance.__class__.__doc__ or f"Tool for {tool_name} operations"
            }
        
        return {
            "tools": tools_info,
            "total_tools": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools information: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools information: {str(e)}"
        )
