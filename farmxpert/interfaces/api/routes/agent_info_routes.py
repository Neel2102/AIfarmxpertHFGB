"""
Agent Information API Routes
Provides information about Indian agents and their capabilities
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from farmxpert.services.agent_config_service import agent_config_service

router = APIRouter(prefix="/agents", tags=["agent-info"])

@router.get("/list")
async def list_all_agents():
    """Get list of all agents with their Indian names and details"""
    try:
        agents = agent_config_service.get_all_agents()
        agent_list = []
        
        for agent_key, agent_config in agents.items():
            agent_list.append({
                "key": agent_key,
                "indian_name": agent_config.get("indian_name", agent_key),
                "full_name": agent_config.get("full_name", agent_key),
                "role": agent_config.get("role", "Agent"),
                "description": agent_config.get("description", "AI Agent"),
                "avatar": agent_config.get("avatar", "🤖"),
                "expertise": agent_config.get("expertise", [])
            })
        
        return {
            "agents": agent_list,
            "total_count": len(agent_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")

@router.get("/categories")
async def get_agent_categories():
    """Get agent categories and their agents"""
    try:
        categories = agent_config_service.get_categories()
        category_list = []
        
        for category_key, category_config in categories.items():
            agents = agent_config_service.get_agents_by_category(category_key)
            category_list.append({
                "key": category_key,
                "name": category_config.get("name", category_key),
                "description": category_config.get("description", ""),
                "color": category_config.get("color", "#666666"),
                "agents": agents,
                "agent_count": len(agents)
            })
        
        return {
            "categories": category_list,
            "total_categories": len(category_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/category/{category}")
async def get_agents_by_category(category: str):
    """Get agents by specific category"""
    try:
        agents = agent_config_service.get_agents_by_category(category)
        category_config = agent_config_service.get_categories().get(category, {})
        
        return {
            "category": {
                "key": category,
                "name": category_config.get("name", category),
                "description": category_config.get("description", ""),
                "color": category_config.get("color", "#666666")
            },
            "agents": agents,
            "agent_count": len(agents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents for category: {str(e)}")

@router.get("/search")
async def search_agents(q: str = Query(..., description="Search query")):
    """Search agents by name, role, or expertise"""
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        results = agent_config_service.search_agents(q)
        
        return {
            "query": q,
            "results": results,
            "result_count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{agent_name}")
async def get_agent_details(agent_name: str):
    """Get detailed information about a specific agent"""
    try:
        agent_info = agent_config_service.get_agent_display_info(agent_name)
        
        if not agent_info:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}")

@router.get("/indian-name/{indian_name}")
async def get_agent_by_indian_name(indian_name: str):
    """Get agent information by Indian name"""
    try:
        agent_info = agent_config_service.get_agent_by_indian_name(indian_name)
        
        if not agent_info:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent by Indian name: {str(e)}")

@router.get("/{agent_name}/expertise")
async def get_agent_expertise(agent_name: str):
    """Get expertise areas for a specific agent"""
    try:
        expertise = agent_config_service.get_expertise(agent_name)
        
        return {
            "agent": agent_name,
            "indian_name": agent_config_service.get_indian_name(agent_name),
            "expertise": expertise,
            "expertise_count": len(expertise)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent expertise: {str(e)}")

@router.get("/status/active")
async def get_active_agents():
    """Get list of currently active agents (for UI display)"""
    try:
        # This would integrate with the actual agent registry
        # For now, return all configured agents
        agents = agent_config_service.get_all_agents()
        active_agents = []
        
        for agent_key, agent_config in agents.items():
            active_agents.append({
                "key": agent_key,
                "indian_name": agent_config.get("indian_name", agent_key),
                "full_name": agent_config.get("full_name", agent_key),
                "role": agent_config.get("role", "Agent"),
                "avatar": agent_config.get("avatar", "🤖"),
                "status": "active",  # This would be dynamic in a real implementation
                "last_activity": "2025-01-01T00:00:00Z"  # This would be dynamic
            })
        
        return {
            "active_agents": active_agents,
            "total_active": len(active_agents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active agents: {str(e)}")
