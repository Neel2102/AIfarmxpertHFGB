"""
FarmXpert AI Platform - Main FastAPI Application
Modular Monolith Architecture with Orchestrator Pattern
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from farmxpert.app.orchestrator.router import router as orchestrator_router
from farmxpert.app.orchestrator.dynamic_router import router as dynamic_router
from farmxpert.app.agents.weather_watcher.router import router as weather_router
from farmxpert.app.agents.growth_stage_monitor.router import router as growth_router
from farmxpert.app.agents.soil_health.router import router as soil_health_router
from farmxpert.app.agents.market_intelligence.router import router as market_intelligence_router

from farmxpert.app.agents.profit_agent.router import router as profit_router
from farmxpert.app.agents.profit_agent.router import router as profit_router
from farmxpert.app.agents.yield_predictor.router import router as yield_router
from farmxpert.app.routers.farm import router as farm_router
from farmxpert.app.routers.system import router as system_router

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

# Mount agent routers
app.include_router(
    orchestrator_router, 
    prefix="/orchestrator",
    tags=["Orchestrator"]
)

app.include_router(
    dynamic_router,
    prefix="/dynamic",
    tags=["Dynamic Data"]
)

app.include_router(
    weather_router, 
    prefix="/agents/weather",
    tags=["Weather Watcher"]
)

app.include_router(
    growth_router, 
    prefix="/agents/growth",
    tags=["Growth Stage Monitor"]
)

app.include_router(
    soil_health_router,
    prefix="/agents/soil_health",
    tags=["Soil Health"]
)

app.include_router(
    market_intelligence_router,
    prefix="/agents/market_intelligence",
    tags=["Market Intelligence"]
)

app.include_router(
    profit_router,
    prefix="/agents/profit",
    tags=["Profit Agent"]
)

app.include_router(
    yield_router,
    prefix="/agents/yield",
    tags=["Yield Predictor"]
)

app.include_router(
    farm_router,
    prefix="/api/farms",
    tags=["Farms"]
)

app.include_router(
    system_router,
    prefix="/api/system",
    tags=["System"]
)

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "FarmXpert AI Platform",
        "version": "1.0.0",
        "architecture": "Modular Monolith",
        "agents": {
            "weather_watcher": "/agents/weather",
            "growth_stage_monitor": "/agents/growth",
            "soil_health": "/agents/soil_health",
            "market_intelligence": "/agents/market_intelligence",
            "profit_agent": "/agents/profit",
            "yield_predictor": "/agents/yield"
        },
        "orchestrator": "/orchestrator",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2026-01-30T11:33:00Z",
        "agents": {
            "weather_watcher": "active",
            "growth_stage_monitor": "active",
            "soil_health": "active",
            "profit_agent": "active",
            "yield_predictor": "active",
            "orchestrator": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
