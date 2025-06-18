"""
Database configuration and session management for the Amazon Product Analyzer.

This module provides SQLAlchemy setup, async database sessions, and
connection management utilities.
"""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Create the SQLAlchemy base class
Base = declarative_base()

# Create async engine for database operations
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.database_echo,
    future=True,
)

# Create sync engine for migrations and admin tasks
sync_engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync session factory for migrations
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    
    Yields:
        AsyncSession: Database session for async operations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """
    Get sync database session for migrations and admin tasks.
    
    Returns:
        Session: Database session for sync operations.
    """
    db = SyncSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_database():
    """
    Initialize database tables.
    
    This function creates all tables defined in models.
    Should be called during application startup.
    """
    async with async_engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from ..models import product, analysis
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """
    Close database connections.
    
    Should be called during application shutdown.
    """
    await async_engine.dispose() 