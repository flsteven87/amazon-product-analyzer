"""
Redis client configuration and connection management.

This module provides Redis connection setup, caching utilities, and
real-time data exchange functionality for the Amazon Product Analyzer.
"""

import json
from typing import Any, Optional, Union
import aioredis
from redis import Redis

from .config import settings


class RedisClient:
    """
    Redis client wrapper with async and sync support.
    
    Provides caching, real-time data exchange, and session management
    functionality using Redis.
    """
    
    def __init__(self):
        self.async_client: Optional[aioredis.Redis] = None
        self.sync_client: Optional[Redis] = None
    
    async def connect_async(self) -> None:
        """
        Initialize async Redis connection.
        """
        self.async_client = aioredis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    
    def connect_sync(self) -> None:
        """
        Initialize sync Redis connection.
        """
        self.sync_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    
    async def disconnect_async(self) -> None:
        """
        Close async Redis connection.
        """
        if self.async_client:
            await self.async_client.close()
    
    def disconnect_sync(self) -> None:
        """
        Close sync Redis connection.
        """
        if self.sync_client:
            self.sync_client.close()
    
    async def set_cache(
        self,
        key: str,
        value: Union[str, dict, list],
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        Set cache value with optional expiration.
        
        Args:
            key (str): Cache key.
            value (Union[str, dict, list]): Value to cache.
            expire_seconds (Optional[int]): Expiration time in seconds.
        
        Returns:
            bool: True if set successfully.
        """
        if not self.async_client:
            await self.connect_async()
        
        # Serialize complex objects to JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        result = await self.async_client.set(key, value, ex=expire_seconds)
        return bool(result)
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cache value and attempt JSON deserialization.
        
        Args:
            key (str): Cache key.
        
        Returns:
            Optional[Any]: Cached value or None if not found.
        """
        if not self.async_client:
            await self.connect_async()
        
        value = await self.async_client.get(key)
        if value is None:
            return None
        
        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def delete_cache(self, key: str) -> bool:
        """
        Delete cache entry.
        
        Args:
            key (str): Cache key to delete.
        
        Returns:
            bool: True if deleted successfully.
        """
        if not self.async_client:
            await self.connect_async()
        
        result = await self.async_client.delete(key)
        return bool(result)
    
    async def set_analysis_progress(
        self,
        session_id: str,
        agent_name: str,
        progress: int,
        status: str = "running"
    ) -> None:
        """
        Update analysis progress for real-time tracking.
        
        Args:
            session_id (str): Analysis session ID.
            agent_name (str): Name of the agent reporting progress.
            progress (int): Progress percentage (0-100).
            status (str): Current status of the agent.
        """
        progress_key = f"analysis_progress:{session_id}"
        progress_data = {
            "agent": agent_name,
            "progress": progress,
            "status": status,
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})
        }
        
        await self.set_cache(progress_key, progress_data, expire_seconds=3600)  # 1 hour
        
        # Publish to subscribers for real-time updates
        channel = f"progress_updates:{session_id}"
        await self.async_client.publish(channel, json.dumps(progress_data))
    
    async def get_analysis_progress(self, session_id: str) -> Optional[dict]:
        """
        Get current analysis progress.
        
        Args:
            session_id (str): Analysis session ID.
        
        Returns:
            Optional[dict]: Progress data or None if not found.
        """
        progress_key = f"analysis_progress:{session_id}"
        return await self.get_cache(progress_key)
    
    async def subscribe_to_progress(self, session_id: str):
        """
        Subscribe to real-time progress updates.
        
        Args:
            session_id (str): Analysis session ID.
        
        Returns:
            PubSub: Redis PubSub object for listening to updates.
        """
        if not self.async_client:
            await self.connect_async()
        
        pubsub = self.async_client.pubsub()
        await pubsub.subscribe(f"progress_updates:{session_id}")
        return pubsub


# Global Redis client instance
redis_client = RedisClient() 