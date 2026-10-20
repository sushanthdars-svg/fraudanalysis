"""
Main FastAPI application initialization and configuration.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.db.database import get_engine
from app.db.base import Base
from app.api import auth, transactions, fraud_rules, fraud_assessment, alert_management, alert_dashboard, analytics, users
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Financial Risk Analysis and Hybrid Fraud Detection System",
    description="Production-grade fraud detection and risk scoring system",
    version="1.0.0",
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    openapi_url="/api/openapi.json" if settings.is_development else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }

# Include routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(fraud_rules.router)
app.include_router(fraud_assessment.router)
app.include_router(alert_management.router)
app.include_router(alert_dashboard.router)
app.include_router(analytics.router)
app.include_router(users.router)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if not settings.is_development else str(exc),
            "status_code": 500,
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and log startup."""
    logger.info(f"Starting application in {settings.environment} mode")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    try:
        # Create tables (in production, use Alembic migrations)
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down application")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )

