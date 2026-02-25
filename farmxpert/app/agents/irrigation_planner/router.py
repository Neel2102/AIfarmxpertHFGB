from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from farmxpert.app.agents.irrigation_planner.agent import IrrigationPlannerAgent
from farmxpert.app.agents.unified_chat import add_chat_endpoint

router = APIRouter()
agent = IrrigationPlannerAgent()

# Add unified chat endpoint
add_chat_endpoint(router, agent, "Irrigation Planner")

class IrrigationPlannerRequest(BaseModel):
    query: str = Field(..., description="User query about irrigation")
    context: Optional[Dict[str, Any]] = Field(None, description="Context (soil data, weather, etc.)")
    tools: Optional[Dict[str, Any]] = Field(None, description="Enabled tools")
    field_size_acres: Optional[float] = Field(None, description="Field size in acres")

@router.post("/plan")
async def plan_irrigation(request: IrrigationPlannerRequest):
    try:
        inputs = request.dict()
        if request.context:
            inputs.update(request.context)
        
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
