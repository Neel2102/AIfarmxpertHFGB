"""
FarmXpert Master Multi-Agent Orchestrator
Coordinates authenticated user context, intent routing, tool permissions,
real tool execution, Gemini interpretation with strict scope control,
response validation, and execution logging.
"""

from __future__ import annotations
import uuid
import time
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from farmxpert.models.user_models import User
from farmxpert.services.orchestrator.farm_context import (
    FarmContext, FarmContextResolver, FarmResolutionStatus, FarmResolutionResult
)
from farmxpert.services.orchestrator.intent_router import (
    intent_router, IntentType, RoutedIntent, AgentPolicy
)
from farmxpert.services.orchestrator.tool_registry import (
    tool_registry, ToolExecutionResult
)
from farmxpert.services.gemini_service import gemini_service
from farmxpert.config.settings import settings
from farmxpert.core.utils.logger import get_logger

logger = get_logger("orchestrator")


class FarmXpertOrchestrator:
    """
    FarmXpert central multi-agent orchestrator.
    Deterministic backend controls authentication, authorization, context, tools, and error handling.
    Gemini is used for intent reasoning and natural language interpretation.
    """

    def __init__(self):
        self.tool_registry = tool_registry
        self.intent_router = intent_router
        self.context_resolver = FarmContextResolver()

    async def process_request(
        self,
        message: str,
        user: User,
        db: Session,
        session_id: Optional[str] = None,
        requested_farm_id: Optional[int] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user request through the full multi-agent orchestration pipeline.
        """
        request_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        start_time = time.perf_counter()

        logger.info(
            f"[ORCHESTRATOR START] req_id={request_id} user_id={user.id} query={message[:60]!r}"
        )

        # ----------------------------------------------------------------------
        # STEP 1: Route Intent
        # ----------------------------------------------------------------------
        routed: RoutedIntent = self.intent_router.route_query(message, chat_history)

        # Handle ambiguous query early (STEP 3)
        if routed.is_ambiguous:
            logger.info(f"[ORCHESTRATOR] Ambiguous query detected: req_id={request_id}")
            return self._build_response(
                intent=routed.primary_intent.value,
                agent="ClarificationAgent",
                response=routed.clarification_message or "Could you please clarify your agricultural question?",
                tool_calls=[],
                context_used=[],
                session_id=session_id,
                duration_ms=(time.perf_counter() - start_time) * 1000.0
            )

        # ----------------------------------------------------------------------
        # STEP 2: Resolve Authenticated Farm Context
        # ----------------------------------------------------------------------
        resolution: FarmResolutionResult = self.context_resolver.resolve(
            db=db,
            user=user,
            requested_farm_id=requested_farm_id,
            query=message
        )

        # Handle authorization violation (STEP 5)
        if resolution.status == FarmResolutionStatus.UNAUTHORIZED:
            logger.warning(f"[ORCHESTRATOR] Unauthorized farm access: req_id={request_id} user={user.id}")
            return self._build_response(
                intent=routed.primary_intent.value,
                agent="SecurityGuard",
                response=resolution.message or "Access denied: Farm does not belong to your account.",
                tool_calls=[],
                context_used=[],
                session_id=session_id,
                success=False,
                duration_ms=(time.perf_counter() - start_time) * 1000.0
            )

        # Handle multi-farm selection needed (STEP 13)
        if resolution.status == FarmResolutionStatus.NEEDS_SELECTION:
            logger.info(f"[ORCHESTRATOR] Farm selection required: req_id={request_id} farms={len(resolution.available_farms)}")
            return self._build_response(
                intent=routed.primary_intent.value,
                agent="FarmSelector",
                response=resolution.message or "Please select which farm you are asking about.",
                tool_calls=[],
                context_used=["available_farms"],
                session_id=session_id,
                duration_ms=(time.perf_counter() - start_time) * 1000.0
            )

        # Handle user has no registered farm (STEP 17)
        farm_context = resolution.context
        if resolution.status == FarmResolutionStatus.NO_FARM:
            # If query specifically asked for farm-specific operations (weather, irrigation, tasks)
            if routed.primary_intent in (IntentType.WEATHER, IntentType.IRRIGATION, IntentType.TASK_SCHEDULING, IntentType.FARM_STATUS):
                return self._build_response(
                    intent=routed.primary_intent.value,
                    agent="OnboardingAgent",
                    response="Please add a farm to your FarmXpert account before requesting farm-specific data.",
                    tool_calls=[],
                    context_used=[],
                    session_id=session_id,
                    duration_ms=(time.perf_counter() - start_time) * 1000.0
                )

        # ----------------------------------------------------------------------
        # STEP 3: Execute Tools Deterministically
        # ----------------------------------------------------------------------
        tool_results: List[ToolExecutionResult] = []
        tools_to_run = routed.tools_needed

        # Extract arguments for tools based on intent & query
        tool_args = self._extract_tool_args(routed.primary_intent, message, farm_context)

        for tool_name in tools_to_run:
            args = tool_args.get(tool_name, {})
            t_res = await self.tool_registry.execute_tool(
                tool_name=tool_name,
                farm_context=farm_context,
                db=db,
                arguments=args
            )
            tool_results.append(t_res)

        # ----------------------------------------------------------------------
        # STEP 4: Handle Tool Failures (STEP 17)
        # ----------------------------------------------------------------------
        failed_tools = [tr for tr in tool_results if not tr.success]
        for ft in failed_tools:
            logger.warning(f"[ORCHESTRATOR TOOL FAIL] tool={ft.tool_name} err={ft.error}")
            # If Weather tool failed, return clean notification without generic advice
            if ft.tool_name == "get_farm_weather":
                err_msg = ft.error or "The weather service is temporarily unavailable for your farm. Please try again shortly."
                return self._build_response(
                    intent=routed.primary_intent.value,
                    agent=routed.selected_agent,
                    response=err_msg,
                    tool_calls=[{"tool": ft.tool_name, "status": "failed", "duration_ms": ft.duration_ms}],
                    context_used=["farm_location"] if farm_context else [],
                    session_id=session_id,
                    duration_ms=(time.perf_counter() - start_time) * 1000.0
                )

        # ----------------------------------------------------------------------
        # STEP 5: Synthesize Response with LLM & Strict Scope Control (STEP 10 & 11)
        # ----------------------------------------------------------------------
        final_answer = await self._generate_scoped_response(
            query=message,
            routed=routed,
            farm_context=farm_context,
            tool_results=tool_results,
            chat_history=chat_history
        )

        # ----------------------------------------------------------------------
        # STEP 6: Validate Response against Forbidden Scope
        # ----------------------------------------------------------------------
        cleaned_answer = self._validate_response_scope(final_answer, routed.policy)

        # ----------------------------------------------------------------------
        # STEP 7: Execution Logging & Structured Response
        # ----------------------------------------------------------------------
        total_duration = (time.perf_counter() - start_time) * 1000.0
        tool_call_records = [
            {"tool": tr.tool_name, "status": "success" if tr.success else "failed", "duration_ms": tr.duration_ms}
            for tr in tool_results
        ]

        logger.info(
            f"[ORCHESTRATOR COMPLETE] req_id={request_id} intent={routed.primary_intent.value} "
            f"agent={routed.selected_agent} tools_executed={len(tool_results)} duration_ms={total_duration:.1f}"
        )

        context_used = []
        if farm_context:
            context_used.append("farm_location")
            if farm_context.soil_type:
                context_used.append("soil_type")
            if farm_context.crops:
                context_used.append("crops")

        return self._build_response(
            intent=routed.primary_intent.value,
            agent=routed.selected_agent,
            response=cleaned_answer,
            tool_calls=tool_call_records,
            context_used=context_used,
            session_id=session_id,
            duration_ms=round(total_duration, 2)
        )

    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------

    def _extract_tool_args(
        self,
        intent: IntentType,
        query: str,
        farm_context: Optional[FarmContext]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract tool arguments from query and context."""
        q_lower = query.lower()
        args: Dict[str, Dict[str, Any]] = {}

        if intent == IntentType.WEATHER:
            forecast_days = 1
            if any(w in q_lower for w in ["tomorrow", "next 2 days", "2 days"]):
                forecast_days = 2
            elif any(w in q_lower for w in ["week", "7 days", "weekly"]):
                forecast_days = 7
            elif any(w in q_lower for w in ["3 days", "few days"]):
                forecast_days = 3
            args["get_farm_weather"] = {"forecast_days": forecast_days}

        elif intent == IntentType.IRRIGATION:
            args["get_farm_weather"] = {"forecast_days": 2}
            args["get_soil_data"] = {}

        elif intent == IntentType.MARKET_PRICES:
            # Extract commodity name
            common_crops = [
                "cotton", "wheat", "rice", "paddy", "soybean", "maize", "corn",
                "groundnut", "mustard", "onion", "potato", "tomato", "chilli",
                "gram", "tur", "moong", "urad", "sugarcane"
            ]
            found_crop = "Cotton"
            for c in common_crops:
                if c in q_lower:
                    found_crop = c.capitalize()
                    break
            args["get_market_prices"] = {
                "commodity": found_crop,
                "location": farm_context.district if farm_context else None
            }

        return args

    async def _generate_scoped_response(
        self,
        query: str,
        routed: RoutedIntent,
        farm_context: Optional[FarmContext],
        tool_results: List[ToolExecutionResult],
        chat_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """
        Generate response using Gemini or high-accuracy deterministic formatter.
        Strictly prevents generic farming advice.
        """
        # If no tools were run (e.g. general greeting/conversation), answer directly
        if not tool_results:
            if routed.primary_intent == IntentType.GENERAL_FARMING:
                prompt = (
                    f"You are FarmXpert, a helpful agricultural assistant. "
                    f"User question: {query}\n"
                    f"Answer concisely and politely. Do not give unsolicited generic advice."
                )
                try:
                    res = await gemini_service.generate_response(prompt, {"task": "general_farming"})
                    if res and not self._is_error_stub(res):
                        return res.strip()
                except Exception:
                    pass
                return "Hello! I am FarmXpert. How can I assist you with your farm operations today?"

        # Format tool outputs for prompt
        tool_data_blocks = []
        for tr in tool_results:
            tool_data_blocks.append(f"Tool: {tr.tool_name}\nData: {json.dumps(tr.data, indent=2, default=str)}")
        all_tool_data = "\n\n".join(tool_data_blocks)

        # Prepare strict scoped prompt (STEP 10 & 21)
        forbidden_rules = ""
        if routed.policy and routed.policy.forbidden_topics:
            forbidden_rules = f"\nFORBIDDEN TOPICS: Do NOT mention or recommend: {', '.join(routed.policy.forbidden_topics)} unless directly asked."

        system_instruction = f"""You are FarmXpert's {routed.selected_agent}.
Your job is to answer the farmer's question using ONLY the provided real-time tool data.

STRICT RULES:
1. Answer the user's actual question directly and concisely.
2. Use the provided tool results. NEVER fabricate or invent weather, market, or sensor numbers.
3. Do NOT provide generic farming advice (no soil testing, no NPK, no drip irrigation, no seeds, no mandi prices) unless specifically requested.{forbidden_rules}
4. If this is a weather query, focus exclusively on the weather (temperature, humidity, rain chance, wind, condition, alerts).
5. Speak in a respectful, professional agricultural advisor tone.
6. Do not mention internal IDs or tool names.
"""

        prompt = f"""{system_instruction}

Farmer Question: "{query}"

Farm Context:
{json.dumps(farm_context.scoped_for_intent(routed.primary_intent.value) if farm_context else {}, indent=2)}

Real Tool Results:
{all_tool_data}

Response:"""

        # Try generating response via Gemini
        try:
            response = await gemini_service.generate_response(prompt, {"task": "orchestrated_response"})
            if response and not self._is_error_stub(response):
                return response.strip()
        except Exception as e:
            logger.warning(f"Gemini generation error: {e}. Falling back to deterministic formatter.")

        # Deterministic formatting fallback (Ensures 100% resilience and zero hallucination)
        return self._format_deterministic_response(routed, tool_results, farm_context)

    def _format_deterministic_response(
        self,
        routed: RoutedIntent,
        tool_results: List[ToolExecutionResult],
        farm_context: Optional[FarmContext]
    ) -> str:
        """Deterministic formatter that presents real tool data cleanly without any generic advice."""
        # 1. WEATHER FORMATTER (STEP 10)
        weather_res = next((tr for tr in tool_results if tr.tool_name == "get_farm_weather" and tr.success), None)
        if weather_res:
            data = weather_res.data
            loc_name = data.get("location", {}).get("name") or "your farm"
            current = data.get("current")
            forecast = data.get("forecast", [])

            lines = [f"**Weather updates for {loc_name}:**\n"]
            if current:
                lines.append(f"• **Temperature:** {current.get('temperature_c')}°C")
                lines.append(f"• **Condition:** {str(current.get('condition', '')).capitalize()}")
                lines.append(f"• **Humidity:** {current.get('humidity_percent')}%")
                lines.append(f"• **Rain Probability:** {current.get('rain_probability_percent')}%")
                if current.get("rainfall_mm"):
                    lines.append(f"• **Expected Rainfall:** {current.get('rainfall_mm')} mm")
                if current.get("wind_speed_kmh"):
                    lines.append(f"• **Wind Speed:** {current.get('wind_speed_kmh')} km/h")

            if forecast:
                lines.append("\n**Upcoming Forecast:**")
                for day in forecast[:3]:
                    lines.append(
                        f"• {day.get('date')}: {day.get('temperature_min_c')}°C – {day.get('temperature_max_c')}°C, "
                        f"{str(day.get('condition', '')).capitalize()} ({day.get('rain_probability_percent')}% rain chance)"
                    )

            return "\n".join(lines)

        # 2. MARKET FORMATTER
        market_res = next((tr for tr in tool_results if tr.tool_name == "get_market_prices" and tr.success), None)
        if market_res:
            data = market_res.data
            comm = data.get("commodity", "Commodity")
            loc = data.get("location", "APMC")
            prices = data.get("prices", [])

            if prices:
                lines = [f"**Current APMC Mandi Prices for {comm} ({loc}):**\n"]
                for p in prices[:3]:
                    lines.append(
                        f"• **{p.get('market')}:** Modal Price ₹{p.get('modal_price_per_quintal')}/quintal "
                        f"(Range: ₹{p.get('min_price')} – ₹{p.get('max_price')})"
                    )
                return "\n".join(lines)
            elif data.get("message"):
                return data["message"]

        # 3. SOIL HEALTH FORMATTER
        soil_res = next((tr for tr in tool_results if tr.tool_name == "get_soil_data" and tr.success), None)
        if soil_res:
            data = soil_res.data
            m = data.get("measurements", {})
            if m:
                lines = [f"**Soil Health Status for Farm #{data.get('farm_id')}:**\n"]
                if "ph" in m: lines.append(f"• **pH Level:** {m['ph']}")
                if "moisture" in m: lines.append(f"• **Soil Moisture:** {m['moisture']}%")
                if "nitrogen" in m: lines.append(f"• **Nitrogen (N):** {m['nitrogen']} mg/kg")
                if "phosphorus" in m: lines.append(f"• **Phosphorus (P):** {m['phosphorus']} mg/kg")
                if "potassium" in m: lines.append(f"• **Potassium (K):** {m['potassium']} mg/kg")
                if "ec" in m: lines.append(f"• **Electrical Conductivity (EC):** {m['ec']} µS/cm")
                return "\n".join(lines)
            return "No recent soil lab test or sensor records found for this farm. You can log a soil test in your Farm Profile."

        return "I have processed your operational request with live farm data."

    def _validate_response_scope(self, text: str, policy: Optional[AgentPolicy]) -> str:
        """
        Validate response against forbidden topics and strip out unauthorized generic advice.
        (STEP 10 & 11)
        """
        if not text or not policy:
            return text

        # If WeatherAgent: strictly ensure no unsolicited advice paragraphs were appended
        if policy.primary_intent == IntentType.WEATHER:
            # Check for generic advice sentences
            forbidden_phrases = [
                "conduct a soil test",
                "soil test to identify precise",
                "balanced n-p-k",
                "implement precision drip",
                "certified disease-resistant seed",
                "monitor daily apmc mandi",
                "avoid over-application of synthetic nitrogen",
                "always verify mandi modal prices",
                "conduct a comprehensive soil test",
                "use certified seeds",
                "test your soil"
            ]
            lines = text.split("\n")
            filtered_lines = []
            for line in lines:
                line_lower = line.lower()
                if any(phrase in line_lower for phrase in forbidden_phrases):
                    logger.info(f"[SCOPE ENFORCEMENT] Stripped generic advice phrase from Weather response: {line[:50]}")
                    continue
                filtered_lines.append(line)
            return "\n".join(filtered_lines).strip()

        return text

    def _is_error_stub(self, text: str) -> bool:
        """Check if Gemini response indicates a rate-limit or provider error."""
        if not text:
            return True
        t = text.lower()
        return any(phrase in t for phrase in [
            "server error", "too many requests", "resource_exhausted",
            "quota exceeded", "limit for now", "temporarily unavailable"
        ])

    def _build_response(
        self,
        intent: str,
        agent: str,
        response: str,
        tool_calls: List[Dict[str, Any]],
        context_used: List[str],
        session_id: str,
        success: bool = True,
        duration_ms: float = 0.0
    ) -> Dict[str, Any]:
        """Build standardized internal orchestrator response (STEP 15)."""
        return {
            "success": success,
            "intent": intent,
            "agent": agent,
            "tool_calls": tool_calls,
            "context_used": context_used,
            "response": response,
            "session_id": session_id,
            "duration_ms": duration_ms
        }


# Global instance
farmxpert_orchestrator = FarmXpertOrchestrator()
