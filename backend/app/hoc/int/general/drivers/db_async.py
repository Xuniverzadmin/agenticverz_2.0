# capability_id: CAP-006
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any (async contexts)
#   Execution: async
# Role: Async SQLAlchemy session factory for non-blocking DB operations
# Callers: Async API routes, async services
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Infrastructure

"""
Async SQLAlchemy session factory for non-blocking DB operations.

This module provides async database access using SQLAlchemy 2.0+ async support
with asyncpg driver. Use this for all new async code paths.

Usage:
    from app.db_async import get_async_session, AsyncSessionLocal

    # As context manager
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Model))

    # With dependency injection
    async def endpoint(session: AsyncSession = Depends(get_async_session)):
        ...

Environment Variables:
    DATABASE_URL_ASYNC: Async database URL (postgresql+asyncpg://...)
    DATABASE_URL: Falls back to sync URL and converts to async format
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger("nova.db_async")


def get_async_database_url() -> str:
    """
    Get async database URL from environment.

    Tries DATABASE_URL_ASYNC first, then converts DATABASE_URL to async format.
    Handles sslmode parameter conversion for asyncpg compatibility.
    """
    async_url = os.getenv("DATABASE_URL_ASYNC")
    if async_url:
        return async_url

    # Convert sync URL to async format
    sync_url = os.getenv("DATABASE_URL")
    if not sync_url:
        raise RuntimeError("DATABASE_URL_ASYNC or DATABASE_URL environment variable is required")

    # Convert postgresql:// to postgresql+asyncpg://
    if sync_url.startswith("postgresql://"):
        result = sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif sync_url.startswith("postgres://"):
        result = sync_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        raise RuntimeError(f"Unsupported database URL format: {sync_url[:20]}...")

    # asyncpg uses 'ssl' instead of 'sslmode', convert the parameter
    # sslmode=require -> ssl=require (asyncpg interprets this correctly)
    result = result.replace("sslmode=", "ssl=")

    return result


# Async engine configuration
DATABASE_URL_ASYNC = get_async_database_url()

# Create async engine with connection pooling
# For async, we use NullPool in some scenarios or configure pool properly
# IMPORTANT: prepared_statement_cache_size=0 is required for PgBouncer compatibility
# PgBouncer in transaction mode doesn't support prepared statements properly
async_engine: AsyncEngine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
    connect_args={
        "prepared_statement_cache_size": 0,  # Required for PgBouncer
        "statement_cache_size": 0,  # Also disable statement cache
    },
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection helper for FastAPI.

    Usage:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for async session.

    Usage:
        async with async_session_context() as session:
            result = await session.execute(select(Model))
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def init_async_db() -> None:
    """
    Initialize async database connection.

    Call this on application startup to verify connectivity.
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Async database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to async database: {e}")
        raise


async def close_async_db() -> None:
    """
    Close async database connections.

    Call this on application shutdown.
    """
    await async_engine.dispose()
    logger.info("Async database connections closed")
