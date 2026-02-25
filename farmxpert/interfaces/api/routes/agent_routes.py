from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import asyncio
import time
import json
from farmxpert.core.base_agent.agent_registry import list_agents, create_agent


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


def _safe_list_str(items: Any, max_items: int = 4) -> List[str]:
    if not isinstance(items, list):
        return []
    out: List[str] = []
    for x in items:
        s = str(x).strip()
        if not s:
            continue
        out.append(s)
        if len(out) >= max_items:
            break
    return out


def _build_farmer_response_text(agent_name: str, response_text: str, payload: Dict[str, Any]) -> str:
    """Normalize agent responses into a consistent, farmer-friendly format.

    This is deterministic (no extra LLM call) and reduces one-liner / repetitive outputs.
    """
    base = (response_text or "").strip()

    # Collect potential reasons
    reasons: List[str] = []
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if isinstance(data, dict):
        detailed = data.get("detailed_reasoning")
        if isinstance(detailed, dict):
            for k in ("weather_impact", "soil_impact", "water_impact", "market_impact", "fertilizer_impact"):
                v = detailed.get(k)
                if isinstance(v, str) and v.strip():
                    reasons.append(v.strip())

        for k in ("reasoning", "analysis_summary", "llm_explanation", "summary"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                reasons.append(v.strip())

    reasons = [r for i, r in enumerate(reasons) if r and r not in reasons[:i]]

    # Collect actions
    recommendations = _safe_list_str(payload.get("recommendations"), max_items=4)
    next_steps = _safe_list_str(payload.get("next_steps"), max_items=4)
    actions = recommendations + [s for s in next_steps if s not in recommendations]

    warnings = _safe_list_str(payload.get("warnings"), max_items=4)

    # Build a consistent message
    parts: List[str] = []
    if base:
        parts.append("Direct Answer:\n" + base)
    else:
        parts.append("Direct Answer:\nI can help, but I need a bit more detail to give the best advice.")

    if reasons:
        parts.append("\nReasons:\n" + "\n".join([f"- {r}" for r in reasons[:3]]))

    if actions:
        parts.append("\nWhat to do now:\n" + "\n".join([f"- {a}" for a in actions[:4]]))

    if warnings:
        parts.append("\nWarnings:\n" + "\n".join([f"- {w}" for w in warnings[:4]]))

    # A light clarifying question to reduce repetitive outputs next turn
    follow_up = payload.get("follow_up_question")
    if not isinstance(follow_up, str) or not follow_up.strip():
        # Agent-specific defaults
        if "crop" in agent_name:
            follow_up = "Which state/district is your farm in, and what is your current season (Kharif/Rabi)?"
        elif "soil" in agent_name:
            follow_up = "Do you have pH and N-P-K values from a soil test or sensor?"
        elif "weather" in agent_name:
            follow_up = "What is your village/district (or share latitude/longitude) so I can localize the forecast?"
        elif "market" in agent_name:
            follow_up = "Which crop and which nearby mandi do you usually sell at?"
        else:
            follow_up = "What is your location and which crop are you referring to?"

    parts.append("\nNext question:\n" + str(follow_up).strip())
    return "\n".join(parts).strip()


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


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def get_agents() -> Dict[str, str]:
    return list_agents()


@router.post("/smoke-test")
async def smoke_test_agents(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body = body or {}
    requested_agents = body.get("agents")
    timeout_s = float(body.get("timeout_s") or 25)

    all_agents = list(list_agents().keys())
    agents: List[str] = all_agents
    if isinstance(requested_agents, list) and requested_agents:
        agents = [a for a in requested_agents if isinstance(a, str)]

    common_context = {
        "location": {"state": "Gujarat", "district": "Surat", "latitude": 21.1702, "longitude": 72.8311},
        "season": "Kharif",
        "land_size_acre": 3,
        "risk_preference": "Low",
        "farm_location": "Surat, Gujarat",
        "farm_size": "3 acres",
        "current_season": "Rainy",
    }

    def _payload_for(agent_name: str) -> Dict[str, Any]:
        if agent_name == "crop_selector":
            return {"query": "What crops should I plant this season?", "context": common_context}
        if agent_name == "seed_selection":
            return {"query": "Which seed variety is best for cotton?", "context": {**common_context, "crop": "cotton"}}
        if agent_name == "soil_health":
            return {
                "query": "Analyze my soil health",
                "context": {
                    **common_context,
                    "soil_data": {
                        "pH": 7.1,
                        "nitrogen": 45,
                        "phosphorus": 18,
                        "potassium": 110,
                        "electrical_conductivity": 1.2,
                        "moisture": 32,
                        "temperature": 26,
                    },
                },
            }
        if agent_name == "fertilizer_advisor":
            return {
                "query": "Suggest fertilizer schedule",
                "context": {**common_context, "soil_data": {"pH": 7.1, "N": 45, "P": 18, "K": 110}, "crop": "cotton"},
            }
        if agent_name == "irrigation_planner":
            return {
                "query": "Plan irrigation schedule",
                "context": {**common_context, "crop": "cotton", "soil_type": "loamy", "weather": {"temperature": 30, "humidity": 70}},
            }
        if agent_name == "weather_watcher":
            return {"query": "Weather forecast for next 7 days", "context": {**common_context, "farm_location": "Surat, Gujarat"}}
        if agent_name == "growth_monitor":
            return {"query": "What should I do at 25 days after sowing?", "context": {**common_context, "crop": "cotton", "days_after_sowing": 25}}
        if agent_name == "market_intelligence":
            return {"query": "Current cotton price trend", "context": {**common_context, "crop": "cotton", "market": "Surat"}}
        if agent_name == "task_scheduler":
            return {"query": "Schedule farm tasks this week", "context": {**common_context, "crop": "cotton", "tasks": ["weeding", "irrigation", "spraying"]}}
        if agent_name == "pest_diagnostic":
            return {"query": "Leaves have spots and curling", "context": {**common_context, "crop": "cotton", "symptoms": "spots and curling"}}

        if agent_name == "yield_predictor":
            return {
                "query": "Predict yield",
                "context": {
                    **common_context,
                    "yield_request": {
                        "State_Name": "Gujarat",
                        "District_Name": "Surat",
                        "Crop": "Cotton",
                        "Season": "Kharif",
                        "Crop_Year": 2024,
                        "Area": 1.0,
                    },
                },
            }

        if agent_name == "profit_optimization":
            return {
                "query": "Optimize profit",
                "context": {
                    **common_context,
                    "crop": "cotton",
                    "area_acre": 3,
                    "yield_per_acre": 8,
                    "expenses": [
                        {"name": "seed", "amount": 1500},
                        {"name": "fertilizer", "amount": 2200},
                        {"name": "labor", "amount": 3000},
                    ],
                    "market_prices": {"Surat": 6200, "Bharuch": 6050},
                },
            }

        return {"query": "Smoke test", "context": common_context}

    async def _run_one(a: str) -> Dict[str, Any]:
        start = time.time()
        try:
            agent = create_agent(a)
        except KeyError:
            return {"agent": a, "ok": False, "error": "Unknown agent"}

        payload = _payload_for(a)
        try:
            res = await asyncio.wait_for(agent.handle(payload), timeout=timeout_s)
            if isinstance(res, dict):
                has_error_flag = bool(res.get("error")) and res.get("success") is not True
                ok = bool(res.get("success", True)) and not has_error_flag
                response = res.get("response")
                if response is None and res.get("message"):
                    response = res.get("message")
                if response is None and res.get("error"):
                    response = str(res.get("error"))
            else:
                ok = True
                response = None
            return {
                "agent": a,
                "ok": ok,
                "elapsed_s": round(time.time() - start, 3),
                "response": (response[:160] if isinstance(response, str) else response),
            }
        except Exception as e:
            return {"agent": a, "ok": False, "elapsed_s": round(time.time() - start, 3), "error": str(e)[:300]}

    results = await asyncio.gather(*[_run_one(a) for a in agents])
    bad = [r["agent"] for r in results if not r.get("ok")]
    return {
        "ok": len(bad) == 0,
        "total": len(results),
        "bad": bad,
        "results": results,
    }


@router.post("/{agent_name}")
async def invoke_agent(agent_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        agent = create_agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

    res = await agent.handle(inputs)
    if not isinstance(res, dict):
        return {"success": True, "response": res}

    success = bool(res.get("success", True)) and not bool(res.get("error"))

    data_for_ui = res.get("data") if isinstance(res.get("data"), dict) else res

    response_text = res.get("response")
    if response_text is None and res.get("natural_language"):
        response_text = res.get("natural_language")
    if response_text is None and res.get("answer"):
        response_text = res.get("answer")
    if response_text is None and res.get("message"):
        response_text = res.get("message")
    if response_text is None and res.get("error"):
        response_text = str(res.get("error"))

    # Many agents return only structured data under `data` and no natural language field.
    # In that case, attempt to extract a meaningful text from nested keys.
    if response_text is None and isinstance(data_for_ui, dict):
        response_text = _find_first_key(
            data_for_ui,
            [
                "response",
                "natural_language",
                "answer",
                "message",
                "summary",
                "llm_explanation",
                "analysis_summary",
            ],
        )

    # Last-resort fallback: provide a compact JSON snippet instead of a hardcoded placeholder.
    if response_text is None and success and isinstance(data_for_ui, dict):
        try:
            response_text = json.dumps(data_for_ui, ensure_ascii=False)[:800]
        except Exception:
            response_text = str(data_for_ui)[:800]

    if response_text is None:
        response_text = "Response ready." if success else "Sorry, something went wrong."

    # Farmer-friendly formatting for consistent UX
    try:
        if isinstance(response_text, str):
            response_text = _build_farmer_response_text(agent_name=agent_name, response_text=response_text, payload=res)
    except Exception:
        # Never fail the request due to formatting
        pass
    ui = _build_smart_chat_ui(
        answer_text=str(response_text) if isinstance(response_text, str) else "Response ready.",
        agent_name=agent_name,
        success=success,
        data=data_for_ui,
        error=str(res.get("error")) if res.get("error") else None,
    )

    return {**res, "ui": ui, "response": response_text}


