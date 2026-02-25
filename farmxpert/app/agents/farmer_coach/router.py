from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from farmxpert.app.agents.farmer_coach.agent import FarmerCoachAgent
from farmxpert.app.agents.unified_chat import add_chat_endpoint

router = APIRouter()
agent = FarmerCoachAgent()

# Add unified chat endpoint
add_chat_endpoint(router, agent, "Farmer Coach")

class FarmerCoachRequest(BaseModel):
    query: str = Field(..., description="User query like 'What should I plant?' or 'Tell me about PM-Kisan'")
    context: Optional[Dict[str, Any]] = Field(None, description="Context (location, language)")
    language: Optional[str] = Field("English", description="Language for response")

@router.post("/ask")
async def ask_coach(request: FarmerCoachRequest):
    try:
        inputs = request.dict()
        if request.context:
            inputs.update(request.context)
        
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
