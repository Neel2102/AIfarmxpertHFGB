from __future__ import annotations
from typing import List, Dict, Any
from .intent_engine import IntentResult
from farmxpert.services.gemini_service import gemini_service
import json


class ResponseSynthesizer:
    """Synthesizes responses from agent outputs into coherent, user-friendly responses"""
    
    async def synthesize_response(self, intent_result: IntentResult, agent_responses: Dict[str, Any], query: str) -> str:
        """Synthesize a coherent response from agent outputs via Gemini (JSON), fallback to legacy."""
        try:
            prompt = self._build_llm_prompt(query, intent_result, agent_responses)
            llm_text = await gemini_service.generate_response(prompt, {"agent": "response_synthesizer"})
            parsed = self._parse_json(llm_text)
            if parsed and isinstance(parsed, dict) and parsed.get("response"):
                return parsed.get("response")
        except Exception:
            pass
        return self.synthesize(query, {"agent_outputs": agent_responses}, intent_result)

    def _build_llm_prompt(self, query: str, intent_result: IntentResult, agent_responses: Dict[str, Any]) -> str:
        safe_outputs = {}
        for k, v in agent_responses.items():
            try:
                safe_outputs[k] = v
            except Exception:
                safe_outputs[k] = str(v)
        return f"""
You are FarmXpert's meta-synthesizer. Combine multiple agent outputs into one concise, actionable message for farmers.

User query: {query}
Intent: {intent_result.intent_type.value} (confidence {intent_result.confidence})
Agent outputs (JSON): {json.dumps(safe_outputs)[:8000]}

Return STRICT JSON with keys:
{{
  "response": "final farmer-facing markdown text",
  "recommendations": ["..."],
  "warnings": ["..."],
  "insights": ["..."]
}}
Only output JSON.
"""

    def _parse_json(self, text: str) -> Dict[str, Any] | None:
        try:
            if not text:
                return None
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end <= start:
                return None
            return json.loads(text[start:end])
        except Exception:
            return None
    
    def synthesize(self, query: str, workflow_output: Dict[str, Any], intent_result: IntentResult) -> str:
        """Fallback synthesis: Prefer agent-authored responses, minimally aggregated."""
        agent_outputs = workflow_output.get("agent_outputs", {})
        texts: List[str] = []
        for agent_name, wrapped in agent_outputs.items():
            # Orchestrator wraps as { response: <agent_payload>, success, execution_time }
            payload = wrapped.get("response") if isinstance(wrapped, dict) else wrapped
            if isinstance(payload, str) and payload.strip():
                texts.append(payload.strip())
            elif isinstance(payload, dict):
                r = payload.get("response")
                if isinstance(r, str) and r.strip():
                    texts.append(r.strip())
        # Deduplicate and limit
        if texts:
            seen = set()
            unique = []
            for t in texts:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)
            return "\n\n".join(unique[:3])
        return "No response generated."