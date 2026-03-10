from fastapi import APIRouter
from typing import Any, Dict

from farmxpert.services.gemini_service import gemini_service
from farmxpert.app.shared.utils import create_success_response


router = APIRouter(prefix="/llm", tags=["llm-usage"])


@router.get("/usage/summary")
async def llm_usage_summary() -> Dict[str, Any]:
    return create_success_response(gemini_service.get_usage_summary())


@router.get("/usage/recent")
async def llm_usage_recent() -> Dict[str, Any]:
    return create_success_response({"events": gemini_service.get_recent_usage()})
