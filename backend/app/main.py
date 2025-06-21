"""Main FastAPI application for Amazon Product Analyzer."""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger
from app.services.database import database_service

# Import simple WebSocket manager
try:
    from app.core.websocket_simple import simple_ws_manager
    WEBSOCKET_AVAILABLE = True
    logger.info("Simple WebSocket manager loaded successfully")
except Exception as e:
    logger.warning(f"WebSocket not available, continuing without it: {e}")
    simple_ws_manager = None
    WEBSOCKET_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info(
        "application_startup",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        api_prefix=settings.API_V1_STR,
        environment=settings.ENVIRONMENT.value,
        allowed_origins=settings.ALLOWED_ORIGINS,
    )
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Amazon Product Analyzer API with Multi-Agent Analysis",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# Add validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from request data."""
    logger.error(
        "validation_error",
        client_host=request.client.host if request.client else "unknown",
        path=request.url.path,
        errors=str(exc.errors()),
    )

    # Format the errors to be more user-friendly
    formatted_errors = []
    for error in exc.errors():
        loc = " -> ".join([str(loc_part) for loc_part in error["loc"] if loc_part != "body"])
        formatted_errors.append({"field": loc, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": formatted_errors},
    )


# Set up CORS middleware
logger.info(
    "configuring_cors",
    allowed_origins=settings.ALLOWED_ORIGINS,
    environment=settings.ENVIRONMENT.value,
    credentials_allowed=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# WebSocket is now handled through API routes
if WEBSOCKET_AVAILABLE and simple_ws_manager:
    logger.info("WebSocket endpoints available at /api/v1/websocket/ws")
else:
    logger.info("WebSocket not available - using HTTP polling only")


@app.get("/")
async def root():
    """Root endpoint returning basic API information."""
    logger.info("root_endpoint_called")
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT.value,
        "swagger_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with database connectivity check."""
    logger.info("health_check_called")

    # Check database connectivity
    db_healthy = await database_service.health_check()

    response = {
        "status": "healthy" if db_healthy else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "components": {"api": "healthy", "database": "healthy" if db_healthy else "unhealthy"},
        "timestamp": datetime.now().isoformat(),
    }

    # If DB is unhealthy, set the appropriate status code
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response, status_code=status_code)


@app.get("/cors-test")
async def cors_test():
    """Simple endpoint to test CORS configuration."""
    logger.info("cors_test_called")
    return {
        "message": "CORS test successful",
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "environment": settings.ENVIRONMENT.value,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/cors-test")
async def cors_test_post():
    """Simple POST endpoint to test CORS preflight requests."""
    logger.info("cors_test_post_called")
    return {
        "message": "CORS POST test successful",
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "environment": settings.ENVIRONMENT.value,
        "timestamp": datetime.now().isoformat(),
    }
