from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from farmxpert.agents.analytics.profit_agent.agent import profit_optimization_agent

router = APIRouter()

class ProfitRequest(BaseModel):
    crop: str
    area_acre: float
    yield_per_acre: float

@router.post("/optimize")
async def optimize_profit(request: ProfitRequest):
    try:
        result = profit_optimization_agent(
            crop=request.crop,
            area_acre=request.area_acre,
            yield_per_acre=request.yield_per_acre
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
