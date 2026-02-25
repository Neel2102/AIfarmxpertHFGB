from pydantic import BaseModel, Field
from typing import List, Dict, Any


class OrchestrateResponse(BaseModel):
    summary: str = Field(...)
    steps: List[str] = Field(default_factory=list)
    details: Dict[str, Any] | None = None


