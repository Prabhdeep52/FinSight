"""
Main FastAPI application for FinSight financial agent system.
Entry point for the financial data API service with AI capabilities.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.finance_routes import router as financial_router
from routes.agent_routes import router as agent_router
from routes.auth_routes import router as auth_router
from routes.gmail_route import router as gmail_router
from config.settings import get_settings
from core.utils import setup_logger

# Initialize settings and logger
settings = get_settings()
logger = setup_logger(__name__, "INFO" if not settings.debug else "DEBUG")

# Create FastAPI application
fastapi_app = FastAPI(
    title="FinSight LLM-Powered Financial Agent API",
    description="LLM-powered financial analysis API using OpenAI GPT with function calling for intelligent stock analysis",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
fastapi_app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
fastapi_app.include_router(financial_router, prefix="/api/v1", tags=["financial-data"])
fastapi_app.include_router(agent_router, prefix="/api/v1/agent", tags=["llm-agent"])
fastapi_app.include_router(gmail_router, prefix="/api/v1/gmail", tags=["gmail"])


# Root endpoint
@fastapi_app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FinSight LLM-Powered Financial Agent API",
        "version": "2.1.0",
        "status": "running",
        "documentation": "/docs",
        "api_endpoints": {
            "v1": {
                "base": "/api/v1",
                "description": "Direct financial data API",
                "endpoints": ["/stock/{symbol}", "/stocks?symbols=...", "/health"],
            },
            "v1_agent": {
                "base": "/api/v1/agent",
                "description": "LLM-powered natural language financial analysis",
                "endpoints": ["/query", "/health", "/examples"],
            },
        },
    }


# Health check endpoint at root level
@fastapi_app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "FinSight LLM-Powered Financial Agent",
        "version": "2.1.0",
    }


# Startup event
@fastapi_app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("FinSight LLM-Powered Financial Agent API v2.1 starting up...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Phase 1 API (v1): Direct financial data access")
    logger.info(
        "Phase 2 API (v2): LLM-powered natural language analysis using OpenAI GPT"
    )
    logger.info("API documentation available at: /docs")


# Shutdown event
@fastapi_app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("FinSight LLM-Powered Financial Agent API shutting down...")


# Use FastAPI app directly (no Socket.IO)
app = fastapi_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info"
    )
