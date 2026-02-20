# capability_id: CAP-006
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Store health checks
# Callers: health API
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Storage System

# Store Health Probes (M12 Beta Readiness)
"""
Health probes for database and Redis connectivity.

Required for M12 Beta rollout:
- Kubernetes readiness/liveness probes
- Prometheus health metrics
- Graceful degradation signaling

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string
- HEALTH_CHECK_TIMEOUT_SECONDS: Timeout for health checks (default: 5)
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

logger = logging.getLogger("nova.stores.health")

HEALTH_CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "5"))


class HealthStatus(Enum):
    """Health status for a component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a single component."""

    name: str
    status: HealthStatus
    latency_ms: float
    message: str = ""
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details,
        }


@dataclass
class OverallHealth:
    """Overall system health."""

    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: str
    version: str = "1.0.0"

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "components": {k: v.to_dict() for k, v in self.components.items()},
        }


# =============================================================================
# Database Health Probe
# =============================================================================


async def check_database_health(timeout: float = HEALTH_CHECK_TIMEOUT) -> ComponentHealth:
    """
    Check PostgreSQL database connectivity.

    Performs:
    1. Connection test
    2. Simple query (SELECT 1)
    3. Connection pool stats (if available)
    """
    start = time.perf_counter()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNKNOWN,
            latency_ms=0,
            message="DATABASE_URL not configured",
        )

    try:
        import asyncpg

        # Connect with timeout
        conn = await asyncio.wait_for(asyncpg.connect(database_url), timeout=timeout)

        try:
            # Simple query
            result = await asyncio.wait_for(conn.fetchval("SELECT 1"), timeout=timeout)

            latency_ms = (time.perf_counter() - start) * 1000

            if result == 1:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency_ms,
                    message="Connected and responsive",
                    details={
                        "server_version": conn.get_server_version(),
                    },
                )
            else:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message=f"Unexpected query result: {result}",
                )

        finally:
            await conn.close()

    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=f"Connection timeout after {timeout}s",
        )
    except ImportError:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNKNOWN,
            latency_ms=0,
            message="asyncpg not installed",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=str(e),
        )


# =============================================================================
# Redis Health Probe
# =============================================================================


async def check_redis_health(timeout: float = HEALTH_CHECK_TIMEOUT) -> ComponentHealth:
    """
    Check Redis connectivity.

    Performs:
    1. Connection test (PING)
    2. Memory stats
    3. Connected clients count
    """
    start = time.perf_counter()

    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNKNOWN,
            latency_ms=0,
            message="REDIS_URL not configured",
        )

    try:
        import redis.asyncio as redis

        # Connect
        client = redis.from_url(redis_url, socket_timeout=timeout)

        try:
            # PING
            ping_result = await asyncio.wait_for(client.ping(), timeout=timeout)

            latency_ms = (time.perf_counter() - start) * 1000

            if ping_result:
                # Get additional info
                info = await client.info("memory")

                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency_ms,
                    message="Connected and responsive",
                    details={
                        "used_memory_human": info.get("used_memory_human", "unknown"),
                        "connected_clients": info.get("connected_clients", "unknown"),
                    },
                )
            else:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message="PING returned False",
                )

        finally:
            await client.close()

    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=f"Connection timeout after {timeout}s",
        )
    except ImportError:
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNKNOWN,
            latency_ms=0,
            message="redis package not installed",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=str(e),
        )


# =============================================================================
# R2/S3 Health Probe
# =============================================================================


async def check_r2_health(timeout: float = HEALTH_CHECK_TIMEOUT) -> ComponentHealth:
    """
    Check Cloudflare R2 connectivity.

    Performs:
    1. List buckets (lightweight)
    """
    start = time.perf_counter()

    from app.stores import get_r2_bucket, get_r2_client

    r2_client = get_r2_client()
    r2_bucket = get_r2_bucket()

    if not r2_client or not r2_bucket:
        return ComponentHealth(
            name="r2",
            status=HealthStatus.UNKNOWN,
            latency_ms=0,
            message="R2 not configured",
        )

    try:
        # HEAD bucket (lightweight check)
        def _check():
            return r2_client.head_bucket(Bucket=r2_bucket)

        loop = asyncio.get_event_loop()
        await asyncio.wait_for(loop.run_in_executor(None, _check), timeout=timeout)

        latency_ms = (time.perf_counter() - start) * 1000

        return ComponentHealth(
            name="r2",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms,
            message="Connected and bucket accessible",
            details={"bucket": r2_bucket},
        )

    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="r2",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=f"Connection timeout after {timeout}s",
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="r2",
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            message=str(e),
        )


# =============================================================================
# Overall Health Check
# =============================================================================


async def check_health(
    include_database: bool = True,
    include_redis: bool = True,
    include_r2: bool = False,
) -> OverallHealth:
    """
    Check overall system health.

    Args:
        include_database: Check PostgreSQL
        include_redis: Check Redis
        include_r2: Check R2 storage

    Returns:
        OverallHealth with all component statuses
    """
    from datetime import datetime, timezone

    components = {}
    tasks = []

    if include_database:
        tasks.append(("database", check_database_health()))
    if include_redis:
        tasks.append(("redis", check_redis_health()))
    if include_r2:
        tasks.append(("r2", check_r2_health()))

    # Run all checks concurrently
    if tasks:
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for (name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=0,
                    message=str(result),
                )
            else:
                components[name] = result

    # Determine overall status
    if not components:
        overall_status = HealthStatus.UNKNOWN
    elif any(c.status == HealthStatus.UNHEALTHY for c in components.values()):
        overall_status = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in components.values()):
        overall_status = HealthStatus.DEGRADED
    elif all(c.status == HealthStatus.HEALTHY for c in components.values()):
        overall_status = HealthStatus.HEALTHY
    else:
        overall_status = HealthStatus.UNKNOWN

    return OverallHealth(
        status=overall_status,
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =============================================================================
# Readiness/Liveness Probes (for Kubernetes)
# =============================================================================


async def readiness_probe() -> Tuple[bool, dict]:
    """
    Kubernetes readiness probe.

    Checks if the service is ready to receive traffic.
    Returns (is_ready: bool, details: dict)
    """
    health = await check_health(include_database=True, include_redis=True)

    is_ready = health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    return is_ready, health.to_dict()


async def liveness_probe() -> Tuple[bool, dict]:
    """
    Kubernetes liveness probe.

    Checks if the service is alive (not deadlocked).
    More lenient than readiness - only fails if completely broken.

    Returns (is_alive: bool, details: dict)
    """
    # For liveness, we just check that we can respond
    # Database/Redis can be down but service is still "alive"
    return True, {"status": "alive", "timestamp": time.time()}


# =============================================================================
# Prometheus Metrics
# =============================================================================


def _update_health_metrics(health: OverallHealth) -> None:
    """Update Prometheus metrics based on health check results."""
    try:
        from prometheus_client import Gauge

        # Create or get gauges
        db_health = Gauge(
            "nova_database_health",
            "Database health status (1=healthy, 0.5=degraded, 0=unhealthy)",
        )
        redis_health = Gauge(
            "nova_redis_health",
            "Redis health status (1=healthy, 0.5=degraded, 0=unhealthy)",
        )
        db_latency = Gauge(
            "nova_database_latency_ms",
            "Database health check latency in milliseconds",
        )
        redis_latency = Gauge(
            "nova_redis_latency_ms",
            "Redis health check latency in milliseconds",
        )

        status_map = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.DEGRADED: 0.5,
            HealthStatus.UNHEALTHY: 0.0,
            HealthStatus.UNKNOWN: 0.0,
        }

        if "database" in health.components:
            db = health.components["database"]
            db_health.set(status_map[db.status])
            db_latency.set(db.latency_ms)

        if "redis" in health.components:
            r = health.components["redis"]
            redis_health.set(status_map[r.status])
            redis_latency.set(r.latency_ms)

    except ImportError:
        pass  # Prometheus not available


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "HealthStatus",
    "ComponentHealth",
    "OverallHealth",
    "check_health",
    "check_database_health",
    "check_redis_health",
    "check_r2_health",
    "readiness_probe",
    "liveness_probe",
]
