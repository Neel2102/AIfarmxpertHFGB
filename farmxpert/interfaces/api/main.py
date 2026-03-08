from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from farmxpert.config.settings import settings
from farmxpert.interfaces.api.routes import health_routes, agent_routes, farm_routes, auth_routes, agent_info_routes
from farmxpert.interfaces.api.routes import llm_usage_routes
from farmxpert.interfaces.api.routes import blynk_routes
from farmxpert.interfaces.api.routes import soil_routes
from farmxpert.interfaces.api.routes import super_agent_updated  # Import updated super agent
from farmxpert.interfaces.api.middleware.logging_middleware import RequestLoggingMiddleware
from farmxpert.models.database import Base, engine
import farmxpert.models.user_models  # noqa: F401
import farmxpert.models.farm_models  # noqa: F401


# Import the new core agent system
from farmxpert.core.core_agent_updated import process_farm_request
from farmxpert.core.agent_routes import router as core_agent_router

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
    
    # Replace old agent system with new core agent router
    app.include_router(core_agent_router, prefix="/api")
    app.include_router(farm_routes.router, prefix="/api")
    app.include_router(super_agent_updated.router, prefix="/api")  # Use updated super agent
    app.include_router(blynk_routes.router, prefix="/api")
    app.include_router(soil_routes.router, prefix="/api")

    return app


app = create_app()


