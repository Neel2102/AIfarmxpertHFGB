from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from farmxpert.app.agents.seed_selector.agent import SeedSelectionAgent

router = APIRouter()
agent = SeedSelectionAgent()

class SeedSelectionRequest(BaseModel):
    query: str = Field(..., description="User query for seed selection")
    context: Optional[Dict[str, Any]] = Field(None, description="Context (location, crop, goals)")
    tools: Optional[Dict[str, Any]] = Field(None, description="Enabled tools")

@router.post("/select")
async def select_seeds(request: SeedSelectionRequest):
    try:
        inputs = request.dict()
        if request.context:
            inputs.update(request.context)
        
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
