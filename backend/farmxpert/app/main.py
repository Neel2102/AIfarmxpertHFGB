"""
FarmXpert AI Platform - Main FastAPI Application
Updated to use the new core agent system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Initialize logger
logger = logging.getLogger(__name__)

# Import the new core agent system
from farmxpert.core.agent_routes import router as core_agent_router
from farmxpert.core.base_agent.agent_registry import AgentRegistry

# Store startup errors for diagnostics
_startup_error = None
_db_status = "initializing"
from farmxpert.interfaces.api.routes import health_routes, farm_routes, auth_routes, agent_info_routes, agent_routes
from farmxpert.interfaces.api.routes import super_agent
from farmxpert.interfaces.api.routes import llm_usage_routes, blynk_routes, soil_routes, iot_routes, admin_routes
from farmxpert.interfaces.api.routes import chat_routes, market_routes, task_routes
from farmxpert.interfaces.api.middleware.logging_middleware import RequestLoggingMiddleware
import farmxpert.models.user_models  # noqa: F401
import farmxpert.models.farm_models  # noqa: F401
import farmxpert.models.farm_profile_models  # noqa: F401
import farmxpert.models.admin_models  # noqa: F401
import farmxpert.models.blynk_models  # noqa: F401
from farmxpert.models.database import Base, engine
from farmxpert.voice.voice_router import router as voice_router

from farmxpert.app.routers import system as system_router

app = FastAPI(
    title="FarmXpert AI Platform",
    description="AI-powered agricultural monitoring and decision support system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Robust Production CORS configuration
# Explicit origins + regex allow credentials to work with all Vercel previews and production
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
app.include_router(super_agent.router, prefix="/api")
app.include_router(blynk_routes.router, prefix="/api")
app.include_router(soil_routes.router, prefix="/api")
app.include_router(iot_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(chat_routes.router, prefix="/api")
app.include_router(market_routes.router, prefix="/api")
app.include_router(task_routes.router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(system_router.router, prefix="/api/orchestrator")


@app.on_event("startup")
async def _ensure_tables_exist():
    global _startup_error, _db_status
    
    # Log database connection attempt
    try:
        from farmxpert.config.settings import settings
        db_url_obfuscated = settings.database_url
        if "@" in db_url_obfuscated:
            pref, suff = db_url_obfuscated.split("@", 1)
            db_url_obfuscated = f"{pref.split('://')[0]}://****:****@{suff}"
        logger.info(f"Attempting to connect to database: {db_url_obfuscated}")
    except Exception as e:
        logger.warning(f"Could not log connection details: {e}")
        
    try:
        # 1. Create any table that does not exist yet.
        Base.metadata.create_all(bind=engine)

        # 2. Converge pre-existing tables onto the canonical model shape.
        #    create_all() never ALTERs an existing table, so a database created
        #    by an older migration keeps the legacy `farms` columns and breaks
        #    every farm INSERT/SELECT with UndefinedColumn / NotNullViolation.
        from farmxpert.services.schema_guard import reconcile_schema
        changes = reconcile_schema(engine)
        if changes:
            logger.warning("Schema guard reconciled %d drift(s) on startup.", len(changes))

        logger.info("Database tables verified successfully.")
        _db_status = "connected"

    except Exception as e:
        _startup_error = str(e)
        _db_status = "failed"
        logger.error(f"NON-FATAL ERROR: Database connectivity failure: {e}")
        logger.error("The app will continue to run for diagnostic purposes.")
        # We do NOT raise here, allowing the app to stay up so we can check logs/endpoints
        
@app.get("/api/diagnostic")
async def diagnostic():
    """Diagnostic endpoint to reveal startup/DB errors"""
    from farmxpert.config.settings import settings
    
    # Obfuscate DB URL
    db_url = settings.database_url
    if "@" in db_url:
        pref, suff = db_url.split("@", 1)
        db_url = f"{pref.split('://')[0]}://****:****@{suff}"
        
    # Deliberately minimal: this endpoint is public, so it must not disclose
    # the environment variable inventory, the import path or the filesystem
    # layout of the container.
    return {
        "status": "online",
        "database_status": _db_status,
        "startup_error": _startup_error,
        "database_host": db_url.split("@")[-1].split("/")[0] if "@" in db_url else None,
    }

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
