"""
API module for Amazon Product Analyzer backend.

This module provides all FastAPI routers for the application including
product management and analysis endpoints.
"""

from . import products, analysis

__all__ = [
    "products",
    "analysis",
] 