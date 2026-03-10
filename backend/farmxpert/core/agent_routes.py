"""
Agent Router API Routes
Provides REST endpoints for the Core Agent system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from farmxpert.core.core_agent_updated import core_agent, process_farm_request
from farmxpert.core.utils.logger import get_logger

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger("agent_routes")

class AgentRequest(BaseModel):
    """Request model for agent processing"""
    user_input: str = Field(..., description="The user's query or request")
    agent_role: str = Field(..., description="The role/personality to adopt")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")

class AgentResponse(BaseModel):
    """Response model for agent processing"""
    agent: str
    success: bool
    response: str
    recommendations: List[str]
    warnings: List[str]
    next_steps: List[str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]

@router.get("/roles")
async def get_available_agent_roles():
    """
    Get list of available agent roles with their descriptions
    
    Returns:
        Dictionary mapping agent roles to their descriptions
    """
    try:
        agents = core_agent.get_available_agents()
        roles_info = {}
        
        for role in agents:
            agent_info = core_agent.get_agent_info(role)
            if agent_info:
                roles_info[role] = agent_info.get("description", "No description available")
        
        return {
            "available_roles": roles_info,
            "total_count": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent roles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent roles: {str(e)}")

@router.get("/roles/{role}", response_model=Dict[str, Any])
async def get_agent_role_info(role: str):
    """
    Get detailed information about a specific agent role
    
    Args:
        role: The agent role to get information for
        
    Returns:
        Detailed information about the agent role
    """
    try:
        agent_info = core_agent.get_agent_info(role)
        
        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent role '{role}' not found")
        
        return {
            "role": role,
            "info": agent_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent role info for {role}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent role info: {str(e)}")

@router.post("/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Process a user request with the specified agent role
    
    Args:
        request: The agent request containing user input and role
        
    Returns:
        Structured response from the agent
    """
    try:
        logger.info(f"Processing request with agent role: {request.agent_role}")
        
        # Validate agent role
        available_roles = core_agent.get_available_agents()
        if request.agent_role not in available_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid agent role '{request.agent_role}'. Available roles: {', '.join(available_roles)}"
            )
        
        # Process the request
        response = await process_farm_request(
            user_input=request.user_input,
            agent_role=request.agent_role,
            context=request.context,
            session_id=request.session_id
        )
        
        logger.info(f"Successfully processed request with {request.agent_role} agent")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing agent request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.post("/chat")
async def chat_with_agent(
    user_input: str,
    agent_role: str = "farmer_coach",
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
):
    """
    Simple chat endpoint for quick agent interactions
    
    Args:
        user_input: The user's message
        agent_role: The agent role to use (defaults to farmer_coach)
        context: Additional context
        session_id: Session identifier
        
    Returns:
        Simple response from the agent
    """
    try:
        response = await process_farm_request(
            user_input=user_input,
            agent_role=agent_role,
            context=context,
            session_id=session_id
        )
        
        return {
            "response": response["response"],
            "agent": response["agent"],
            "success": response["success"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@router.get("/health")
async def agent_health_check():
    """
    Health check for the agent system
    
    Returns:
        Health status of the agent system
    """
    try:
        available_roles = core_agent.get_available_agents()
        prompts_loaded = len(core_agent.prompts)
        tools_available = len(core_agent.tools)
        
        return {
            "status": "healthy",
            "available_roles": len(available_roles),
            "prompts_loaded": prompts_loaded,
            "tools_available": tools_available,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Example usage documentation
@router.get("/examples", response_model=Dict[str, List[Dict[str, str]]])
async def get_agent_examples():
    """
    Get examples for each agent role to help users understand capabilities
    
    Returns:
        Dictionary mapping agent roles to their examples
    """
    try:
        examples = {}
        available_roles = core_agent.get_available_agents()
        
        for role in available_roles:
            agent_info = core_agent.get_agent_info(role)
            if agent_info and "examples" in agent_info:
                examples[role] = agent_info["examples"]
        
        return {
            "examples": examples,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent examples: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get examples: {str(e)}")
