from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from farmxpert.app.agents.crop_selector.agent import CropSelectorAgent
from farmxpert.app.agents.unified_chat import add_chat_endpoint

router = APIRouter()
agent = CropSelectorAgent()

# Add unified chat endpoint
add_chat_endpoint(router, agent, "Crop Selector")

class CropSelectorRequest(BaseModel):
    query: str = Field(..., description="User query for crop selection")
    location: Optional[Dict[str, Any]] = Field(None, description="Farm location format: {'state': '...', 'district': '...'}")
    season: Optional[str] = Field(None, description="Current season (e.g., Kharif, Rabi)")
    land_size_acre: Optional[float] = Field(None, description="Land size in acres")
    soil_data: Optional[Dict[str, Any]] = Field(None, description="Soil data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

@router.post("/analyze")
async def analyze_crop_selection(request: CropSelectorRequest):
    try:
        inputs = request.dict()
        if request.context:
            inputs.update(request.context)
            inputs["context"] = request.context
        
        return await agent.handle(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
