import os
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from farmxpert.config.settings import settings
from farmxpert.interfaces.api.routes import health_routes, agent_routes, farm_routes, auth_routes, agent_info_routes, chat_routes
from farmxpert.interfaces.api.routes import llm_usage_routes, blynk_routes, soil_routes, iot_routes, admin_routes, task_routes, market_routes
from farmxpert.interfaces.api.routes import super_agent
from farmxpert.interfaces.api.middleware.logging_middleware import RequestLoggingMiddleware
import farmxpert.models.user_models  # noqa: F401
import farmxpert.models.farm_models  # noqa: F401
import farmxpert.models.admin_models  # noqa: F401

# Import the new core agent system
from farmxpert.core.agent_routes import router as core_agent_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse)

    # Add CORS middleware
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://a-ifarmxpert-hfgb-git-c38026-neelsutariya21-gmailcoms-projects.vercel.app",
    ]
    custom_origins = os.getenv("CORS_ORIGINS", "")
    if custom_origins:
        for o in custom_origins.split(","):
            if o.strip():
                allowed_origins.append(o.strip())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health_routes.router, prefix="/api")
    app.include_router(auth_routes.router, prefix="/api")
    app.include_router(agent_info_routes.router, prefix="/api")
    app.include_router(llm_usage_routes.router, prefix="/api")
    
    # Replace old agent system with new core agent router
    app.include_router(agent_routes.router, prefix="/api")
    app.include_router(core_agent_router, prefix="/api")
    app.include_router(farm_routes.router, prefix="/api")
    app.include_router(super_agent.router, prefix="/api")
    app.include_router(blynk_routes.router, prefix="/api")
    app.include_router(soil_routes.router, prefix="/api")
    app.include_router(iot_routes.router, prefix="/api")
    app.include_router(admin_routes.router, prefix="/api")
    app.include_router(chat_routes.router, prefix="/api")
    app.include_router(task_routes.router, prefix="/api")
    app.include_router(market_routes.router, prefix="/api")
    from farmxpert.app.routers import system as system_router
    app.include_router(system_router.router, prefix="/api/orchestrator")

    return app


app = create_app()
