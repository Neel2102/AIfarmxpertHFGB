"""
FarmXpert AI Platform - Main FastAPI Application
Updated to use the new core agent system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Import the new core agent system instead of old scattered agents
from farmxpert.core.core_agent_updated import process_farm_request
from farmxpert.core.agent_routes import router as core_agent_router
from farmxpert.interfaces.api.routes import health_routes, farm_routes, auth_routes, agent_info_routes, agent_routes
from farmxpert.interfaces.api.routes import super_agent_updated
from farmxpert.interfaces.api.routes import llm_usage_routes, blynk_routes, soil_routes, iot_routes, admin_routes
from farmxpert.interfaces.api.routes import chat_routes, market_routes, task_routes
from farmxpert.interfaces.api.middleware.logging_middleware import RequestLoggingMiddleware
import farmxpert.models.user_models  # noqa: F401
import farmxpert.models.farm_models  # noqa: F401
import farmxpert.models.admin_models  # noqa: F401
import farmxpert.models.blynk_models  # noqa: F401
from farmxpert.models.database import Base, engine
from farmxpert.app.orchestrator.router import router as orchestrator_router
from farmxpert.voice.voice_router import router as voice_router

app = FastAPI(
    title="FarmXpert AI Platform",
    description="AI-powered agricultural monitoring and decision support system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Include updated routes
app.include_router(health_routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(agent_info_routes.router, prefix="/api")
app.include_router(llm_usage_routes.router, prefix="/api")

# Replace old agent system with new core agent router
app.include_router(agent_routes.router, prefix="/api")  # This provides /api/agents/{agent_name}
app.include_router(core_agent_router, prefix="/api")    # This provides /api/agent/* endpoints
app.include_router(farm_routes.router, prefix="/api")
app.include_router(super_agent_updated.router, prefix="/api")
app.include_router(blynk_routes.router, prefix="/api")
app.include_router(soil_routes.router, prefix="/api")
app.include_router(iot_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(orchestrator_router, prefix="/api/orchestrator")
app.include_router(chat_routes.router, prefix="/api")
app.include_router(market_routes.router, prefix="/api")
app.include_router(task_routes.router, prefix="/api")
app.include_router(voice_router, prefix="/api")


@app.on_event("startup")
async def _ensure_tables_exist():
    # Log database host for debugging (obfuscated)
    try:
        db_host = engine.url.host
        logger.info(f"Connecting to database host: {db_host}")
    except Exception as e:
        logger.warning(f"Could not log database host: {e}")
        
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")
    except Exception as e:
        logger.error(f"Failed to create/verify database tables: {e}")
        # On Railway, failing here is fatal for the app
        raise e

@app.get("/")
async def root():
    """Root endpoint - API information"""
    from farmxpert.core.core_agent_updated import core_agent
    
    available_agents = core_agent.get_available_agents()
    return {
        "message": "FarmXpert AI Platform",
        "version": "1.0.0",
        "architecture": "Core Agent Router",
        "core_agent": "active",
        "available_agents": len(available_agents),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "agents": "/api/agents",
            "core_agent": "/api/agent",
            "super_agent": "/api/super-agent",
            "chat": "/api/super-agent/chat"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from farmxpert.core.core_agent_updated import core_agent
        
        available_agents = core_agent.get_available_agents()
        
        return {
            "status": "healthy",
            "timestamp": "2026-03-08T12:17:00Z",
            "core_agent": "active",
            "available_agents": len(available_agents),
            "database": "connected",
            "architecture": "Core Agent Router"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2026-03-08T12:17:00Z"
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
