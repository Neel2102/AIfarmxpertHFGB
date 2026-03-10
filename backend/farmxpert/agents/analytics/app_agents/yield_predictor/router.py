from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from farmxpert.agents.crop_planning.yield_predictor.tools.yield_predictor_tool import yield_predictor_tool

router = APIRouter()

class YieldPredictionRequest(BaseModel):
    State_Name: str = Field(..., description="State name")
    District_Name: str = Field(..., description="District name")
    Crop: str = Field(..., description="Crop name")
    Season: str = Field(..., description="Season")
    Crop_Year: int = Field(..., description="Crop year")
    Area: float = Field(..., gt=0, description="Area in hectares")

@router.post("/predict")
async def predict_yield_api(request: YieldPredictionRequest):
    try:
        result = yield_predictor_tool(
            State_Name=request.State_Name,
            District_Name=request.District_Name,
            Crop=request.Crop,
            Season=request.Season,
            Crop_Year=request.Crop_Year,
            Area=request.Area
        )
        return {"predicted_yield": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
