from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from farmxpert.app.agents.compliance.agent import ComplianceCertificationAgent

router = APIRouter()
agent = ComplianceCertificationAgent()

class ComplianceRequest(BaseModel):
    certification_type: str = Field("organic", description="Type of certification (organic, export, government_schemes)")
    farm_size: Optional[float] = Field(0, description="Farm size acres")
    current_practices: Optional[Dict[str, Any]] = Field(None, description="Current farming practices")
    location: Optional[str] = Field("unknown", description="Farm location")

@router.post("/certify")
async def certify_check(request: ComplianceRequest):
    try:
        inputs = request.dict()
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
