from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OrchestrateRequest(BaseModel):
    query: str = Field(..., description="Farmer's question or instruction")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context payload")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")


