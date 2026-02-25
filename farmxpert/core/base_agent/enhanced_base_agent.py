"""
Enhanced Base Agent for FarmXpert
Extends existing agents with LLM capabilities while maintaining compatibility
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from farmxpert.core.base_agent.base_agent import BaseAgent
from farmxpert.core.utils.logger import get_logger
from farmxpert.services.gemini_service import gemini_service


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentPriority(Enum):
    """Agent execution priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EnhancedAgentContext:
    """Enhanced context information for agent execution"""
    session_id: str
    user_id: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[float] = None
    farm_size_unit: str = "hectares"
    preferred_language: str = "en"
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    farm_id: Optional[str] = None
    db_session: Optional[Any] = None


@dataclass
class EnhancedAgentInput:
    """Enhanced input data for agent processing"""
    query: str
    context: EnhancedAgentContext
    additional_data: Dict[str, Any] = field(default_factory=dict)
    priority: AgentPriority = AgentPriority.NORMAL
    timeout: int = 30  # seconds


@dataclass
class EnhancedAgentOutput:
    """Enhanced output data from agent processing"""
    success: bool
    response: str
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedBaseAgent(BaseAgent):
    """
    Enhanced base class for FarmXpert agents
    Adds LLM capabilities while maintaining compatibility with existing agents
    """
    
    def __init__(
        self,
        name: str = None,
        description: str = None,
        use_llm: bool = True,
        max_retries: int = 3,
        temperature: float = 0.6
    ):
        # Use provided values or fall back to class attributes
        self.name = name or getattr(self, 'name', 'enhanced_agent')
        self.description = description or getattr(self, 'description', 'Enhanced AI Agent')
        
        super().__init__()
        
        # Enhanced capabilities
        self.use_llm = use_llm
        self.max_retries = max_retries
        self.temperature = temperature
        self.status = AgentStatus.IDLE
        
        # Enhanced logger
        self.logger = get_logger(f"enhanced_agent.{self.name}")
        
        # Agent-specific configuration
        self.config = self._load_agent_config()
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent-specific configuration"""
        return {
            "max_tokens": 2000,
            "system_prompt": self._get_system_prompt(),
            "examples": self._get_examples(),
            "tools": self._get_tools(),
            "use_llm": self.use_llm
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are {self.name}, a world-class agricultural expert specialized in {self.description}.

Your goal is to provide precise, data-backed, and actionable advice to the farmer.

CORE INSTRUCTIONS:
1.  **Analyze Context**: deep-dive into the provided soil data, weather, and conversation history.
2.  **Reason Step-by-Step**: Before answering, think through the problem. Consider causes, effects, and dependencies.
3.  **Use Tools**: If you have tool outputs (in Context/Data), USE them. Do not hallucinate numbers if real data is available.
4.  **Be Practical**: Farmers need clear steps, not academic theory. Use simple language but expert concepts.
5.  **Memory**: The user may refer to previous messages (e.g., "what about for wheat?"). Use the 'Conversation History' to resolve context.

Response Logic:
- If tool data is present -> Synthesize it into a clear answer.
- If data is missing -> Ask the user for it or provide general advice with a disclaimer.
- If unsure -> Admit it. Do not make up facts.
"""
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example conversations for this agent"""
        return []
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools/functions available to this agent"""
        return []

    def _prepare_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for LLM processing"""
        context = {
            "user_query": inputs.get("query", ""),
            "farm_location": inputs.get("location", ""),
            "season": inputs.get("season", ""),
            "soil_data": inputs.get("soil", {}),
            "chat_history": inputs.get("context", {}).get("chat_history", []), # Capture history
            "additional_data": inputs
        }
        
        # Add any other relevant context from inputs
        for key, value in inputs.items():
            if key not in ["query", "location", "season", "soil", "context"]:
                context[key] = value
        
        return context

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt"""
        if not history:
            return "No previous conversation."
            
        formatted = []
        # Take last 10 turns to maintain context without overflowing token limits
        recent_history = history[-10:] 
        
        for turn in recent_history:
            role = "Farmer" if turn.get("role") == "user" else "Expert"
            content = turn.get("content", "").strip()
            if content:
                formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def _build_prompt(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build the complete prompt for LLM"""
        system_prompt = self.config["system_prompt"]
        examples = self.config["examples"]
        tools = self.config["tools"]
        
        # Build context string
        context_str = self._format_context(context)
        
        # Build history string
        history_str = self._format_history(context.get("chat_history", []))
        
        # Build examples string
        examples_str = self._format_examples(examples)
        
        # Build tools string
        tools_str = self._format_tools(tools)
        
        # Build complete prompt
        prompt = f"""System: {system_prompt}

{tools_str}

{examples_str}

Conversation History:
{history_str}

Current Context:
{context_str}

User Query: {inputs.get('query', '')}

Please provide a comprehensive response in the following JSON format:
{{
    "response": "Main response text (markdown supported)",
    "recommendations": ["recommendation1", "recommendation2"],
    "warnings": ["warning1", "warning2"],
    "insights": ["insight1", "insight2"],
    "data": {{"key": "value"}},
    "confidence": 0.85
}}

Response:"""
        
        return prompt
    
    async def _get_llm_response(self, prompt: str, inputs: Dict[str, Any]) -> str:
        """Get response from LLM with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await gemini_service.generate_response(prompt, {"agent": self.name})
                return response
                
            except Exception as e:
                self.logger.warning(f"LLM request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                parsed = json.loads(json_str)
                
                # Validate required fields
                if "response" not in parsed:
                    parsed["response"] = response
                
                return parsed
            else:
                # Fallback to treating entire response as text
                return {
                    "response": response,
                    "recommendations": [],
                    "warnings": [],
                    "insights": [],
                    "data": {},
                    "confidence": 0.7
                }
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {
                "response": response,
                "recommendations": [],
                "warnings": [],
                "insights": [],
                "data": {},
                "confidence": 0.6
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "use_llm": self.use_llm,
            "enhanced": True
        }
    
    async def reset(self):
        """Reset agent to idle state"""
        self.status = AgentStatus.IDLE
        self.logger.info("Agent reset to idle state")
    
    async def cancel(self):
        """Cancel current processing"""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.CANCELLED
            self.logger.info("Agent processing cancelled")
    
    def enable_llm(self):
        """Enable LLM capabilities"""
        self.use_llm = True
        self.logger.info("LLM capabilities enabled")
    
    def disable_llm(self):
        """Disable LLM capabilities"""
        self.use_llm = False
        self.logger.info("LLM capabilities disabled")
