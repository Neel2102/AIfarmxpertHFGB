from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from farmxpert.config.settings import settings
from farmxpert.interfaces.api.routes import health_routes, agent_routes, farm_routes, auth_routes, agent_info_routes, super_agent
from farmxpert.interfaces.api.routes import llm_usage_routes
from farmxpert.interfaces.api.middleware.logging_middleware import RequestLoggingMiddleware
from farmxpert.models.database import Base, engine
import farmxpert.models.user_models  # noqa: F401


from farmxpert.app.agents.profit_agent.router import router as profit_router
from farmxpert.app.agents.yield_predictor.router import router as yield_router
from farmxpert.app.agents.crop_selector.router import router as crop_selector_router
from farmxpert.app.agents.pest_disease.router import router as pest_disease_router
from farmxpert.app.agents.irrigation_planner.router import router as irrigation_planner_router
from farmxpert.app.agents.seed_selector.router import router as seed_selector_router
from farmxpert.app.agents.farmer_coach.router import router as farmer_coach_router
from farmxpert.app.agents.compliance.router import router as compliance_router
from farmxpert.app.agents.soil_health.router import router as soil_health_router
from farmxpert.app.agents.weather_watcher.router import router as weather_watcher_router
from farmxpert.app.agents.growth_stage_monitor.router import router as growth_stage_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse)

    @app.on_event("startup")
    async def _create_db_tables() -> None:
        Base.metadata.create_all(bind=engine)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health_routes.router, prefix="/api")
    app.include_router(auth_routes.router, prefix="/api")
    app.include_router(agent_info_routes.router, prefix="/api")
    app.include_router(llm_usage_routes.router, prefix="/api")
    # Orchestrator removed; super agent handles routing
    app.include_router(agent_routes.router, prefix="/api")
    app.include_router(farm_routes.router, prefix="/api")
    app.include_router(super_agent.router, prefix="/api")
    
    # Add new agents
    app.include_router(profit_router, prefix="/api/agents/profit", tags=["Profit Agent"])
    app.include_router(yield_router, prefix="/api/agents/yield", tags=["Yield Predictor"])
    app.include_router(crop_selector_router, prefix="/api/agents/crop-selector", tags=["Crop Selector"])
    app.include_router(pest_disease_router, prefix="/api/agents/pest-disease", tags=["Pest & Disease"])
    app.include_router(irrigation_planner_router, prefix="/api/agents/irrigation-planner", tags=["Irrigation Planner"])
    app.include_router(seed_selector_router, prefix="/api/agents/seed-selector", tags=["Seed Selector"])
    app.include_router(farmer_coach_router, prefix="/api/agents/farmer-coach", tags=["Farmer Coach"])
    app.include_router(compliance_router, prefix="/api/agents/compliance", tags=["Compliance"])
    app.include_router(soil_health_router, prefix="/api/agents/soil-health", tags=["Soil Health"])
    app.include_router(weather_watcher_router, prefix="/api/agents/weather-watcher", tags=["Weather Watcher"])
    app.include_router(growth_stage_router, prefix="/api/agents/growth-stage-monitor", tags=["Growth Stage Monitor"])

    return app


app = create_app()


