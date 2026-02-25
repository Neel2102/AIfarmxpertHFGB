import google.generativeai as genai
import asyncio
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, List, AsyncGenerator, Optional
from farmxpert.config.settings import settings
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.redis_cache_service import redis_cache

class GeminiService:
    def __init__(self):
        self.logger = get_logger("gemini_service")
        self.model = None
        self._cache = {}  # Fallback in-memory cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._rate_limit_window_seconds = 60
        self._rate_limit_max_requests = 20
        self._request_timestamps: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        self._usage_events: List[Dict[str, Any]] = []
        self._usage_events_max = 500
        self._usage_lock = asyncio.Lock()
        self._initialize_gemini()

    def _looks_like_sdk_accessor_warning(self, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False
        t = text.lower()
        return (
            "quick accessor" in t
            and "response.text" in t
            and "result.parts" in t
        )

    def _extract_text_from_response(self, response: Any) -> str:
        """Extract plain text from google-generativeai response objects.

        The SDK may return multi-part responses where `response.text` is not usable.
        We prefer candidates[0].content.parts[].text and fall back to `response.text`.
        """
        if response is None:
            return ""

        # First try SDK's convenience attribute if present.
        try:
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip() and not self._looks_like_sdk_accessor_warning(text):
                return text.strip()
        except Exception:
            pass

        # Fallback: dig into candidates/content/parts
        try:
            candidates = getattr(response, "candidates", None)
            if isinstance(candidates, list) and candidates:
                for cand in candidates:
                    content = getattr(cand, "content", None)
                    parts = getattr(content, "parts", None) if content is not None else None
                    if isinstance(parts, list) and parts:
                        chunks: List[str] = []
                        for p in parts:
                            pt = getattr(p, "text", None)
                            if isinstance(pt, str) and pt:
                                chunks.append(pt)
                        out = "".join(chunks).strip()
                        if out:
                            return out
        except Exception:
            pass

        # Final fallback: stringify
        try:
            return str(response).strip()
        except Exception:
            return ""
    
    def _initialize_gemini(self):
        """Initialize Gemini API with fallback models"""
        try:
            if not settings.gemini_api_key:
                self.logger.warning("GEMINI_API_KEY not found in environment variables")
                return
            
            genai.configure(api_key=settings.gemini_api_key)
            
            # Try the configured model first, then fallback models
            fallback_models = [
                settings.gemini_model,
                "gemini-flash-latest",
                "gemini-pro-latest",
                "gemini-pro"
            ]
            
            for model_name in fallback_models:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.logger.info(f"Gemini API initialized successfully with model: {model_name}")
                    return
                except Exception as model_error:
                    self.logger.warning(f"Failed to initialize with model {model_name}: {model_error}")
                    continue
            
            # If all models fail
            self.logger.error("Failed to initialize with any available model")
            self.model = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Gemini API (non-streaming for backward compatibility)"""
        if not self.model:
            return "Gemini API not available. Please check your API key configuration."
        
        try:
            context = context or {}

            bypass_cache = bool(context.get("no_cache"))

            # Check cache first to reduce API usage
            cache_key = self._get_cache_key(prompt, context)
            if not bypass_cache:
                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    await self._record_usage(
                        prompt=prompt,
                        output=cached_response,
                        context=context,
                        cached=True,
                        usage_metadata=None,
                    )
                    return cached_response

            allowed = await self._acquire_rate_limit_slot()
            if not allowed:
                return "I’m getting too many requests right now. Please wait a minute and try again."

            # Build the full prompt with context
            if context.get("raw_prompt"):
                full_prompt = prompt
            else:
                full_prompt = self._build_prompt(prompt, context)
            
            # Generate response
            safety_settings = None
            # Prefer concise JSON responses; cap tokens
            generation_config = {
                "temperature": min(0.4, settings.gemini_temperature or 0.4),
                "max_output_tokens": min(512, settings.gemini_max_output_tokens or 512),
            }
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=settings.gemini_request_timeout
            )
            
            # Ensure trimmed minimal text
            out = self._extract_text_from_response(response)
            if self._looks_like_sdk_accessor_warning(out):
                # Never leak SDK guidance to the user; treat as empty so fallbacks apply.
                out = ""
            await self._record_usage(
                prompt=full_prompt,
                output=out,
                context=context,
                cached=False,
                usage_metadata=getattr(response, "usage_metadata", None),
            )
            if out:
                if not bypass_cache:
                    await self._cache_response(cache_key, out)
            return out
        except Exception as e:
            msg = str(e)
            if "quota exceeded" in msg.lower() or "free_tier_requests" in msg.lower():
                self.logger.warning(f"Gemini quota exceeded: {e}")
                cached_response = await self._get_cached_response(self._get_cache_key(prompt, context or {}))
                if cached_response:
                    return cached_response
                return "I’ve hit the free-tier AI limit for now. Please wait a minute and try again."
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {msg}"

    def get_usage_summary(self) -> Dict[str, Any]:
        """Return aggregated usage counts grouped by agent/task."""
        summary: Dict[str, Any] = {
            "total_calls": 0,
            "total_prompt_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "by_agent": {},
        }

        for ev in self._usage_events:
            summary["total_calls"] += 1
            summary["total_prompt_tokens"] += int(ev.get("prompt_tokens") or 0)
            summary["total_output_tokens"] += int(ev.get("output_tokens") or 0)
            summary["total_tokens"] += int(ev.get("total_tokens") or 0)

            agent = ev.get("agent") or "unknown"
            task = ev.get("task") or "unknown"
            summary["by_agent"].setdefault(agent, {"total_calls": 0, "total_tokens": 0, "by_task": {}})
            summary["by_agent"][agent]["total_calls"] += 1
            summary["by_agent"][agent]["total_tokens"] += int(ev.get("total_tokens") or 0)

            summary["by_agent"][agent]["by_task"].setdefault(task, {"total_calls": 0, "total_tokens": 0})
            summary["by_agent"][agent]["by_task"][task]["total_calls"] += 1
            summary["by_agent"][agent]["by_task"][task]["total_tokens"] += int(ev.get("total_tokens") or 0)

        return summary

    def get_recent_usage(self) -> List[Dict[str, Any]]:
        return list(self._usage_events)[-100:]
    
    async def generate_streaming_response(self, prompt: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini API with caching"""
        if not self.model:
            yield "Gemini API not available. Please check your API key configuration."
            return

        context = context or {}
        bypass_cache = bool(context.get("no_cache"))
        
        # Check cache first
        cache_key = self._get_cache_key(prompt, context)
        cached_response = None if bypass_cache else await self._get_cached_response(cache_key)
        
        if cached_response:
            # Simulate streaming for cached responses
            words = cached_response.split()
            for i, word in enumerate(words):
                if i > 0:
                    yield " "
                yield word
                # Small delay to simulate streaming
                await asyncio.sleep(0.02)
            return

        allowed = await self._acquire_rate_limit_slot()
        if not allowed:
            yield "I’m getting too many requests right now. Please wait a minute and try again."
            return
        
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Optimized generation config for faster responses
            generation_config = {
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_output_tokens,
                "top_p": settings.gemini_top_p,
                "top_k": settings.gemini_top_k,
            }
            
            safety_settings = None
            full_response = ""
            
            # Generate streaming response
            response_stream = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=True
                ),
                timeout=settings.gemini_request_timeout
            )
            
            # Stream the response chunks
            for chunk in response_stream:
                piece = self._extract_text_from_response(chunk)
                if self._looks_like_sdk_accessor_warning(piece):
                    piece = ""
                if piece:
                    full_response += piece
                    yield piece
                    # Small delay to prevent overwhelming the frontend
                    await asyncio.sleep(0.01)
            
            # Cache the complete response
            if full_response:
                if not bypass_cache:
                    await self._cache_response(cache_key, full_response)
                    
        except asyncio.TimeoutError:
            self.logger.error("Gemini API request timed out")
            yield "Request timed out. Please try again with a shorter question."
        except Exception as e:
            msg = str(e)
            if "quota exceeded" in msg.lower() or "free_tier_requests" in msg.lower():
                self.logger.warning(f"Gemini quota exceeded (stream): {e}")
                yield "I’ve hit the free-tier AI limit for now. Please wait a minute and try again."
                return
            self.logger.error(f"Error generating streaming response: {e}")
            yield f"Error generating response: {msg}"
    
    def _get_cache_key(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a cache key for the prompt and context"""
        ctx = context or {}
        cache_data = {
            "prompt": prompt,
            "context": ctx,
            "model": settings.gemini_model,
            "temperature": settings.gemini_temperature,
            "top_p": settings.gemini_top_p,
            "top_k": settings.gemini_top_k
        }

        # If the caller passes a session_id, scope cache to the session to avoid "stuck" responses.
        if isinstance(ctx, dict) and ctx.get("session_id"):
            cache_data["session_id"] = str(ctx.get("session_id"))
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        # Try Redis first
        if await redis_cache.is_available():
            cached_response = await redis_cache.get(cache_key)
            if cached_response:
                self.logger.info(f"Redis cache hit for key: {cache_key[:8]}...")
                return cached_response
        
        # Fallback to in-memory cache
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data["timestamp"] < self._cache_ttl:
                self.logger.info(f"In-memory cache hit for key: {cache_key[:8]}...")
                return cached_data["response"]
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    async def _cache_response(self, cache_key: str, response: str):
        """Cache the response"""
        # Try Redis first
        if await redis_cache.is_available():
            success = await redis_cache.set(cache_key, response, self._cache_ttl)
            if success:
                self.logger.info(f"Redis cached response for key: {cache_key[:8]}...")
                return
        
        # Fallback to in-memory cache
        self._cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        self.logger.info(f"In-memory cached response for key: {cache_key[:8]}...")

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        # Rough heuristic: 1 token ~= 4 chars (works okay for monitoring)
        return max(1, int(len(text) / 4))

    async def _record_usage(
        self,
        prompt: str,
        output: str,
        context: Dict[str, Any],
        cached: bool,
        usage_metadata: Any,
    ) -> None:
        ctx = context or {}
        agent = ctx.get("agent") or ctx.get("agent_id") or ctx.get("agent_name")
        task = ctx.get("task")

        prompt_tokens = None
        output_tokens = None
        total_tokens = None

        if usage_metadata and isinstance(usage_metadata, dict):
            prompt_tokens = usage_metadata.get("prompt_token_count")
            output_tokens = usage_metadata.get("candidates_token_count")
            total_tokens = usage_metadata.get("total_token_count")

        if prompt_tokens is None:
            prompt_tokens = self._estimate_tokens(prompt)
        if output_tokens is None:
            output_tokens = self._estimate_tokens(output)
        if total_tokens is None:
            total_tokens = int(prompt_tokens) + int(output_tokens)

        ev = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "agent": agent,
            "task": task,
            "cached": bool(cached),
            "prompt_tokens": int(prompt_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(total_tokens),
        }

        async with self._usage_lock:
            self._usage_events.append(ev)
            if len(self._usage_events) > self._usage_events_max:
                self._usage_events = self._usage_events[-self._usage_events_max :]

    async def _acquire_rate_limit_slot(self) -> bool:
        if self._rate_limit_max_requests <= 0:
            return True
        now = time.time()
        async with self._rate_limit_lock:
            window_start = now - self._rate_limit_window_seconds
            self._request_timestamps = [t for t in self._request_timestamps if t >= window_start]
            if len(self._request_timestamps) >= self._rate_limit_max_requests:
                return False
            self._request_timestamps.append(now)
            return True
    
    def _build_prompt(self, farmer_question: str, context: Dict[str, Any] = None) -> str:
        """Build a prompt with formatting rules for FarmXpert.

        Notes:
        - For JSON/tooling tasks, we avoid verbose formatting wrappers to reduce token use and parsing failures.
        """

        context = context or {}

        # If the caller expects JSON, keep the wrapper minimal to avoid breaking parsers and wasting tokens.
        wants_json = bool(context.get("format") == "json") or ("format as json" in (farmer_question or "").lower())
        if wants_json:
            return f"""You are FarmXpert, an AI agricultural expert system.

Context (JSON):
{json.dumps(context, ensure_ascii=False)}

Task:
{farmer_question}
"""

        return f"""You are FarmXpert, an AI agricultural expert system.

CRITICAL FORMATTING RULES:
- Use proper line breaks between sections
- Use bullet points (-) for lists
- Each item should be on a new line
- Keep the response short and actionable

Farmer Context:
{json.dumps(context, ensure_ascii=False, indent=2) if context else "No context provided"}

Farmer Question:
{farmer_question}

Provide your response in this EXACT format with proper line breaks:

Direct Answer:
[1-2 short sentences]

Recommendations:
- Recommendation 1
- Recommendation 2
- Recommendation 3

Warnings / Considerations:
- Warning 1
- Warning 2

Next Steps:
- Step 1
- Step 2
"""
    
    async def analyze_soil_data(self, soil_data: Dict[str, Any]) -> str:
        """Analyze soil data using Gemini"""
        prompt = f"""
Analyze this soil data and provide recommendations:
Soil pH: {soil_data.get('ph', 'Unknown')}
Nitrogen (N): {soil_data.get('nitrogen', 'Unknown')} ppm
Phosphorus (P): {soil_data.get('phosphorus', 'Unknown')} ppm
Potassium (K): {soil_data.get('potassium', 'Unknown')} ppm
Organic Matter: {soil_data.get('organic_matter', 'Unknown')}%

Provide analysis in structured plain text format with soil health score, recommendations, suitable crops, and fertilizer needs.
"""
        
        response = await self.generate_response(prompt, {"data_type": "soil_analysis"})
        return response
    
    async def recommend_crops(self, location: str, season: str, soil_data: Dict[str, Any]) -> str:
        """Recommend crops using Gemini"""
        prompt = f"""
Based on the following information, recommend the best crops to plant:

Location: {location}
Season: {season}
Soil Data: {soil_data}

Provide recommendations in structured plain text format with crop suggestions, priorities, expected yields, market analysis, and risk assessment.
"""
        
        response = await self.generate_response(prompt, {"data_type": "crop_recommendation"})
        return response
    
    async def analyze_weather_impact(self, weather_data: Dict[str, Any], crops: List[str]) -> str:
        """Analyze weather impact on crops"""
        prompt = f"""
Analyze the impact of this weather data on the following crops:

Weather Data: {weather_data}
Current Crops: {crops}

Provide analysis in structured plain text format with weather risks, recommended actions, crop vulnerability, and timing recommendations.
"""
        
        response = await self.generate_response(prompt, {"data_type": "weather_analysis"})
        return response
    
    async def optimize_farm_operations(self, farm_data: Dict[str, Any]) -> str:
        """Optimize farm operations"""
        prompt = f"""
Optimize farm operations based on this data:

Farm Size: {farm_data.get('size', 'Unknown')} acres
Current Crops: {farm_data.get('crops', [])}
Available Equipment: {farm_data.get('equipment', [])}
Labor Availability: {farm_data.get('labor', 'Unknown')}
Budget: {farm_data.get('budget', 'Unknown')}

Provide optimization in structured plain text format with task schedules, resource allocation, cost optimization, yield improvement, and risk mitigation.
"""
        
        response = await self.generate_response(prompt, {"data_type": "farm_optimization"})
        return response
    
    async def predict_yield(self, historical_data: Dict[str, Any], current_conditions: Dict[str, Any]) -> str:
        """Predict crop yield"""
        prompt = f"""
Predict crop yield based on:

Historical Data: {historical_data}
Current Conditions: {current_conditions}

Provide prediction in structured plain text format with predicted yield, confidence level, factors affecting yield, improvement recommendations, and risk factors.
"""
        
        response = await self.generate_response(prompt, {"data_type": "yield_prediction"})
        return response
    
    async def analyze_market_trends(self, crop_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Analyze market trends"""
        prompt = f"""
Analyze market trends for:

Crops: {crop_data.get('crops', [])}
Market Data: {market_data}

Provide analysis in structured plain text format with price trends, market opportunities, risk assessment, selling recommendations, and alternative markets.
"""
        
        response = await self.generate_response(prompt, {"data_type": "market_analysis"})
        return response
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini"""
        try:
            if not response:
                return {}
                
            # Check for API errors returned as plain text
            if "Gemini API not available" in response or "limit" in response.lower():
                return {"error": response}

            import json
            # Extract JSON from response if it's wrapped in markdown
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            # Handle standard markdown block without 'json' language tag
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                # Try to find JSON in the response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                else:
                    json_str = response
            
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            # Try to sanitize and parse if common issues exist (common in some LLM outputs)
            try:
                # Sometimes LLMs output single quotes instead of double
                if "'" in response and '"' not in response:
                    import ast
                    return ast.literal_eval(response)
            except:
                pass
                
            return {
                "error": "Failed to parse response",
                # Do not return raw_response to avoid polluting logs/contexts with massive strings
            }

# Global instance
gemini_service = GeminiService()
