"""
Main FastAPI application for Amazon Product Analyzer backend.

This module sets up the FastAPI application with all routes, middleware,
and lifecycle event handlers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .core import settings, init_database, close_database, redis_client
from .api import products, analysis


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for database connections,
    Redis connections, and other resources.
    """
    # Startup
    logger.info("Starting Amazon Product Analyzer backend", version="1.0.0")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize Redis connection
        await redis_client.connect_async()
        logger.info("Redis connection established")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Amazon Product Analyzer backend")
    
    try:
        # Close Redis connection
        await redis_client.disconnect_async()
        logger.info("Redis connection closed")
        
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Amazon product analysis and optimization platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Application health status.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment,
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with basic application information.
    
    Returns:
        dict: Welcome message and API information.
    """
    return {
        "message": "Welcome to Amazon Product Analyzer API",
        "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
        "version": "1.0.0",
        "status": "running",
    }


# Include API routers
app.include_router(
    products.router,
    prefix=settings.api_v1_prefix + "/products",
    tags=["products"],
)

app.include_router(
    analysis.router,
    prefix=settings.api_v1_prefix + "/analysis",
    tags=["analysis"],
)


# Custom exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """
    Handle ValueError exceptions.
    """
    logger.error("ValueError occurred", error=str(exc), path=request.url.path)
    return {"error": "Invalid input", "detail": str(exc), "status_code": 400}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle general exceptions.
    """
    logger.error("Unhandled exception occurred", error=str(exc), path=request.url.path)
    return {"error": "Internal server error", "detail": "An unexpected error occurred", "status_code": 500}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    ) 