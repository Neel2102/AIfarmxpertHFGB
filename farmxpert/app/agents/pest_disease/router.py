from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from farmxpert.app.agents.pest_disease.agent import PestDiseaseDiagnosticAgent
from farmxpert.app.agents.unified_chat import add_chat_endpoint

router = APIRouter()
agent = PestDiseaseDiagnosticAgent()

# Add unified chat endpoint
add_chat_endpoint(router, agent, "Pest & Disease Diagnostic")

class PestDiseaseRequest(BaseModel):
    query: str = Field(..., description="User query describing symptoms")
    tools: Optional[Dict[str, Any]] = Field(None, description="Enabled tools")
    context: Optional[Dict[str, Any]] = Field(None, description="Context (location, previous data)")
    symptoms: Optional[List[str]] = Field(None, description="List of observed symptoms")

@router.post("/diagnose")
async def diagnose_pest_disease(request: PestDiseaseRequest):
    try:
        inputs = request.dict()
        if request.context:
            inputs.update(request.context)
        
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
