"""
Unified chat endpoint for all individual agents.
This module provides a generic /chat endpoint that can be added to any agent router.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class UnifiedChatRequest(BaseModel):
    """Unified request model for all agent chats"""
    query: str = Field(..., description="User's natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")

class UnifiedChatResponse(BaseModel):
    """Unified response model for all agent chats"""
    success: bool
    response: str  # Natural language response
    data: Optional[Dict[str, Any]] = None  # Structured data
    agent_name: str
    session_id: Optional[str] = None

def add_chat_endpoint(router: APIRouter, agent_instance, agent_name: str):
    """
    Add a unified /chat endpoint to an agent router.
    
    Args:
        router: FastAPI router instance
        agent_instance: Agent instance with handle() method
        agent_name: Display name of the agent
    """
    
    @router.post("/chat", response_model=UnifiedChatResponse)
    async def chat(request: UnifiedChatRequest):
        """
        Unified chat endpoint for conversational interaction with the agent.
        Accepts natural language queries and returns natural language responses.
        """
        try:
            # Prepare inputs for agent
            inputs = {
                "query": request.query,
                "context": request.context or {},
                "session_id": request.session_id
            }
            
            # Call agent's handle method
            result = await agent_instance.handle(inputs)
            
            # Extract natural language response
            if isinstance(result, dict):
                # Try to get natural language response
                response_text = (
                    result.get("natural_language") or
                    result.get("response") or
                    result.get("answer") or
                    result.get("message") or
                    str(result)
                )
                
                return UnifiedChatResponse(
                    success=result.get("success", True),
                    response=response_text,
                    data=result,
                    agent_name=agent_name,
                    session_id=request.session_id
                )
            else:
                # Fallback for non-dict responses
                return UnifiedChatResponse(
                    success=True,
                    response=str(result),
                    data={"raw_response": result},
                    agent_name=agent_name,
                    session_id=request.session_id
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"{agent_name} error: {str(e)}"
            )
    
    return router
