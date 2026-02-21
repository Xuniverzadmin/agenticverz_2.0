# capability_id: CAP-012
# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified connection pool manager with health checking
# Callers: Services, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-172 (Connection Pool Management)

"""
Connection Pool Manager (GAP-172)

Manages connection pools for various services with:
- Health checking
- Per-tenant limits
- Metrics
- Graceful shutdown
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class PoolType(str, Enum):
    """Types of connection pools."""

    DATABASE = "database"
    REDIS = "redis"
    HTTP = "http"
    EXTERNAL = "external"


class PoolStatus(str, Enum):
    """Pool health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


@dataclass
class PoolConfig:
    """Configuration for a connection pool."""

    pool_id: str
    pool_type: PoolType
    name: str

    # Connection settings
    min_size: int = 1
    max_size: int = 10
    max_idle_seconds: int = 300
    connection_timeout_seconds: float = 10.0

    # Health check settings
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: float = 5.0

    # Per-tenant limits (if applicable)
    max_connections_per_tenant: Optional[int] = None

    # Connection string or config
    connection_string: Optional[str] = None
    connection_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PoolStats:
    """Statistics for a connection pool."""

    pool_id: str
    pool_type: PoolType
    status: PoolStatus

    # Connection counts
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_requests: int = 0

    # Health
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    last_error: Optional[str] = None

    # Metrics
    total_acquisitions: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    avg_wait_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pool_id": self.pool_id,
            "pool_type": self.pool_type.value,
            "status": self.status.value,
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "waiting_requests": self.waiting_requests,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_failures": self.health_check_failures,
            "last_error": self.last_error,
            "total_acquisitions": self.total_acquisitions,
            "total_releases": self.total_releases,
            "total_timeouts": self.total_timeouts,
            "avg_wait_time_ms": self.avg_wait_time_ms,
        }


@dataclass
class PoolHandle:
    """Handle to a managed connection pool."""

    pool_id: str
    pool_type: PoolType
    config: PoolConfig
    pool: Any  # The actual pool object (asyncpg.Pool, redis.ConnectionPool, etc.)
    stats: PoolStats
    health_check_task: Optional[asyncio.Task] = None
    _closed: bool = False


class ConnectionPoolManager:
    """
    Unified connection pool manager.

    Features:
    - Manages multiple pool types (database, redis, http)
    - Health checking with automatic status updates
    - Per-tenant connection limits
    - Graceful shutdown
    - Metrics collection
    """

    def __init__(self):
        self._pools: Dict[str, PoolHandle] = {}
        self._tenant_connections: Dict[str, Dict[str, int]] = {}  # tenant_id -> pool_id -> count
        self._shutdown_event = asyncio.Event()
        self._started = False

    async def start(self) -> None:
        """Start the pool manager."""
        if self._started:
            return
        self._started = True
        logger.info("ConnectionPoolManager started")

    async def stop(self) -> None:
        """Stop all pools and cleanup."""
        self._shutdown_event.set()

        for pool_id in list(self._pools.keys()):
            await self.close_pool(pool_id)

        self._started = False
        logger.info("ConnectionPoolManager stopped")

    async def create_database_pool(
        self,
        pool_id: str,
        connection_string: Optional[str] = None,
        min_size: int = 1,
        max_size: int = 10,
        max_connections_per_tenant: Optional[int] = None,
    ) -> PoolHandle:
        """
        Create a PostgreSQL connection pool.

        Args:
            pool_id: Unique identifier for this pool
            connection_string: PostgreSQL connection string
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_connections_per_tenant: Per-tenant limit

        Returns:
            PoolHandle
        """
        config = PoolConfig(
            pool_id=pool_id,
            pool_type=PoolType.DATABASE,
            name=f"db-{pool_id}",
            min_size=min_size,
            max_size=max_size,
            connection_string=connection_string or os.getenv("DATABASE_URL"),
            max_connections_per_tenant=max_connections_per_tenant,
        )

        try:
            import asyncpg

            pool = await asyncpg.create_pool(
                dsn=config.connection_string,
                min_size=config.min_size,
                max_size=config.max_size,
                command_timeout=config.connection_timeout_seconds,
            )

            stats = PoolStats(
                pool_id=pool_id,
                pool_type=PoolType.DATABASE,
                status=PoolStatus.HEALTHY,
                total_connections=pool.get_size(),
                idle_connections=pool.get_idle_size(),
            )

            handle = PoolHandle(
                pool_id=pool_id,
                pool_type=PoolType.DATABASE,
                config=config,
                pool=pool,
                stats=stats,
            )

            # Start health check
            handle.health_check_task = asyncio.create_task(
                self._health_check_loop(handle)
            )

            self._pools[pool_id] = handle
            logger.info(f"Created database pool {pool_id} with max_size={max_size}")
            return handle

        except Exception as e:
            logger.error(f"Failed to create database pool {pool_id}: {e}")
            raise

    async def create_redis_pool(
        self,
        pool_id: str,
        redis_url: Optional[str] = None,
        max_connections: int = 10,
    ) -> PoolHandle:
        """
        Create a Redis connection pool.

        Args:
            pool_id: Unique identifier for this pool
            redis_url: Redis connection URL
            max_connections: Maximum connections

        Returns:
            PoolHandle
        """
        config = PoolConfig(
            pool_id=pool_id,
            pool_type=PoolType.REDIS,
            name=f"redis-{pool_id}",
            max_size=max_connections,
            connection_string=redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        )

        try:
            import redis.asyncio as redis

            pool = redis.ConnectionPool.from_url(
                config.connection_string,
                max_connections=config.max_size,
            )

            stats = PoolStats(
                pool_id=pool_id,
                pool_type=PoolType.REDIS,
                status=PoolStatus.HEALTHY,
            )

            handle = PoolHandle(
                pool_id=pool_id,
                pool_type=PoolType.REDIS,
                config=config,
                pool=pool,
                stats=stats,
            )

            handle.health_check_task = asyncio.create_task(
                self._health_check_loop(handle)
            )

            self._pools[pool_id] = handle
            logger.info(f"Created Redis pool {pool_id}")
            return handle

        except Exception as e:
            logger.error(f"Failed to create Redis pool {pool_id}: {e}")
            raise

    async def create_http_pool(
        self,
        pool_id: str,
        base_url: Optional[str] = None,
        max_connections: int = 100,
        timeout_seconds: float = 30.0,
    ) -> PoolHandle:
        """
        Create an HTTP client pool.

        Args:
            pool_id: Unique identifier for this pool
            base_url: Optional base URL for requests
            max_connections: Maximum concurrent connections
            timeout_seconds: Request timeout

        Returns:
            PoolHandle
        """
        import httpx

        config = PoolConfig(
            pool_id=pool_id,
            pool_type=PoolType.HTTP,
            name=f"http-{pool_id}",
            max_size=max_connections,
            connection_timeout_seconds=timeout_seconds,
            connection_config={"base_url": base_url} if base_url else {},
        )

        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_connections // 2,
        )

        client = httpx.AsyncClient(
            base_url=base_url,
            limits=limits,
            timeout=timeout_seconds,
        )

        stats = PoolStats(
            pool_id=pool_id,
            pool_type=PoolType.HTTP,
            status=PoolStatus.HEALTHY,
        )

        handle = PoolHandle(
            pool_id=pool_id,
            pool_type=PoolType.HTTP,
            config=config,
            pool=client,
            stats=stats,
        )

        self._pools[pool_id] = handle
        logger.info(f"Created HTTP pool {pool_id}")
        return handle

    async def get_pool(self, pool_id: str) -> Optional[PoolHandle]:
        """Get a pool by ID."""
        return self._pools.get(pool_id)

    async def acquire_connection(
        self,
        pool_id: str,
        tenant_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Acquire a connection from a pool.

        Args:
            pool_id: Pool identifier
            tenant_id: Tenant identifier (for per-tenant limits)
            timeout: Acquisition timeout

        Returns:
            Connection object

        Raises:
            ValueError: If pool not found
            TimeoutError: If acquisition times out
            RuntimeError: If tenant limit exceeded
        """
        handle = self._pools.get(pool_id)
        if not handle:
            raise ValueError(f"Pool not found: {pool_id}")

        if handle._closed:
            raise RuntimeError(f"Pool is closed: {pool_id}")

        # Check tenant limits
        if tenant_id and handle.config.max_connections_per_tenant:
            current = self._tenant_connections.get(tenant_id, {}).get(pool_id, 0)
            if current >= handle.config.max_connections_per_tenant:
                raise RuntimeError(
                    f"Tenant {tenant_id} exceeded connection limit for pool {pool_id}"
                )

        timeout = timeout or handle.config.connection_timeout_seconds
        start_time = asyncio.get_event_loop().time()

        try:
            if handle.pool_type == PoolType.DATABASE:
                conn = await asyncio.wait_for(
                    handle.pool.acquire(),
                    timeout=timeout,
                )
            elif handle.pool_type == PoolType.REDIS:
                import redis.asyncio as redis
                conn = redis.Redis(connection_pool=handle.pool)
            else:
                conn = handle.pool  # HTTP client is used directly

            # Track tenant connections
            if tenant_id:
                if tenant_id not in self._tenant_connections:
                    self._tenant_connections[tenant_id] = {}
                self._tenant_connections[tenant_id][pool_id] = (
                    self._tenant_connections[tenant_id].get(pool_id, 0) + 1
                )

            # Update stats
            handle.stats.total_acquisitions += 1
            handle.stats.active_connections += 1
            wait_time = (asyncio.get_event_loop().time() - start_time) * 1000
            handle.stats.avg_wait_time_ms = (
                handle.stats.avg_wait_time_ms * 0.9 + wait_time * 0.1
            )

            return conn

        except asyncio.TimeoutError:
            handle.stats.total_timeouts += 1
            raise

    async def release_connection(
        self,
        pool_id: str,
        connection: Any,
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Release a connection back to the pool.

        Args:
            pool_id: Pool identifier
            connection: Connection to release
            tenant_id: Tenant identifier
        """
        handle = self._pools.get(pool_id)
        if not handle:
            return

        try:
            if handle.pool_type == PoolType.DATABASE:
                await handle.pool.release(connection)
            elif handle.pool_type == PoolType.REDIS:
                await connection.close()
            # HTTP client doesn't need explicit release

            # Update tenant tracking
            if tenant_id and tenant_id in self._tenant_connections:
                if pool_id in self._tenant_connections[tenant_id]:
                    self._tenant_connections[tenant_id][pool_id] -= 1
                    if self._tenant_connections[tenant_id][pool_id] <= 0:
                        del self._tenant_connections[tenant_id][pool_id]

            # Update stats
            handle.stats.total_releases += 1
            handle.stats.active_connections = max(0, handle.stats.active_connections - 1)

        except Exception as e:
            logger.warning(f"Error releasing connection to pool {pool_id}: {e}")

    async def close_pool(self, pool_id: str) -> bool:
        """
        Close a pool and release all resources.

        Args:
            pool_id: Pool identifier

        Returns:
            True if closed, False if not found
        """
        handle = self._pools.get(pool_id)
        if not handle:
            return False

        handle._closed = True

        # Cancel health check
        if handle.health_check_task:
            handle.health_check_task.cancel()
            try:
                await handle.health_check_task
            except asyncio.CancelledError:
                pass

        # Close the pool
        try:
            if handle.pool_type == PoolType.DATABASE:
                await handle.pool.close()
            elif handle.pool_type == PoolType.REDIS:
                await handle.pool.disconnect()
            elif handle.pool_type == PoolType.HTTP:
                await handle.pool.aclose()

            handle.stats.status = PoolStatus.CLOSED
            logger.info(f"Closed pool {pool_id}")

        except Exception as e:
            logger.error(f"Error closing pool {pool_id}: {e}")

        del self._pools[pool_id]
        return True

    async def get_stats(self, pool_id: Optional[str] = None) -> Dict[str, PoolStats]:
        """
        Get pool statistics.

        Args:
            pool_id: Optional specific pool ID

        Returns:
            Dict of pool_id -> PoolStats
        """
        if pool_id:
            handle = self._pools.get(pool_id)
            if handle:
                return {pool_id: handle.stats}
            return {}

        return {pid: h.stats for pid, h in self._pools.items()}

    async def health_check(self, pool_id: str) -> PoolStatus:
        """
        Perform health check on a pool.

        Args:
            pool_id: Pool identifier

        Returns:
            PoolStatus
        """
        handle = self._pools.get(pool_id)
        if not handle:
            return PoolStatus.UNHEALTHY

        try:
            if handle.pool_type == PoolType.DATABASE:
                async with handle.pool.acquire() as conn:
                    await conn.execute("SELECT 1")

            elif handle.pool_type == PoolType.REDIS:
                import redis.asyncio as redis
                client = redis.Redis(connection_pool=handle.pool)
                await client.ping()
                await client.close()

            elif handle.pool_type == PoolType.HTTP:
                # HTTP pools don't need explicit health check
                pass

            handle.stats.status = PoolStatus.HEALTHY
            handle.stats.health_check_failures = 0
            handle.stats.last_health_check = datetime.now(timezone.utc)
            handle.stats.last_error = None

            return PoolStatus.HEALTHY

        except Exception as e:
            handle.stats.health_check_failures += 1
            handle.stats.last_error = str(e)
            handle.stats.last_health_check = datetime.now(timezone.utc)

            if handle.stats.health_check_failures >= 3:
                handle.stats.status = PoolStatus.UNHEALTHY
            else:
                handle.stats.status = PoolStatus.DEGRADED

            logger.warning(f"Health check failed for pool {pool_id}: {e}")
            return handle.stats.status

    async def _health_check_loop(self, handle: PoolHandle) -> None:
        """Background health check loop for a pool."""
        while not self._shutdown_event.is_set() and not handle._closed:
            try:
                await asyncio.sleep(handle.config.health_check_interval_seconds)
                if not handle._closed:
                    await self.health_check(handle.pool_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error for {handle.pool_id}: {e}")

    def list_pools(self) -> list[str]:
        """List all pool IDs."""
        return list(self._pools.keys())
