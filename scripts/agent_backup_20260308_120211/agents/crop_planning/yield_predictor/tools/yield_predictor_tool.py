
from pydantic import BaseModel, Field

from farmxpert.agents.crop_planning.yield_predictor.models.yield_model import predict_yield


class YieldPredictionInput(BaseModel):
    State_Name: str = Field(..., description="State name")
    District_Name: str = Field(..., description="District name")
    Crop: str = Field(..., description="Crop name")
    Season: str = Field(..., description="Season")
    Crop_Year: int = Field(..., description="Crop year")
    Area: float = Field(..., gt=0, description="Area in hectares")


def yield_predictor_tool(
    State_Name: str,
    District_Name: str,
    Crop: str,
    Season: str,
    Crop_Year: int,
    Area: float,
):
    payload = {
        "State_Name": State_Name,
        "District_Name": District_Name,
        "Crop": Crop,
        "Season": Season,
        "Crop_Year": Crop_Year,
        "Area": Area,
    }
    return predict_yield(payload)
