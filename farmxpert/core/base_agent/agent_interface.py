from __future__ import annotations
from typing import Protocol, Any, Dict


class AgentInterface(Protocol):
    name: str
    description: str

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ...


