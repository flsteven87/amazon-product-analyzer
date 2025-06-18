"""
Core module for Amazon Product Analyzer backend.

This module provides essential infrastructure components including
configuration, database, and Redis client setup.
"""

from .config import settings
from .database import (
    Base,
    get_async_db,
    get_sync_db,
    init_database,
    close_database,
    AsyncSessionLocal,
    SyncSessionLocal,
)
from .redis_client import redis_client

__all__ = [
    "settings",
    "Base",
    "get_async_db",
    "get_sync_db", 
    "init_database",
    "close_database",
    "AsyncSessionLocal",
    "SyncSessionLocal",
    "redis_client",
] 