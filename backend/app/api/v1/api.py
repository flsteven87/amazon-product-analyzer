"""API router configuration."""

from fastapi import APIRouter

from app.api.v1 import product_analysis
from app.core.logging import logger

api_router = APIRouter()

# Include product analysis routes
api_router.include_router(product_analysis.router, prefix="/product-analysis", tags=["product-analysis"])


# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("health_check_called")
    return {"status": "healthy", "service": "amazon-product-analyzer-api"}
