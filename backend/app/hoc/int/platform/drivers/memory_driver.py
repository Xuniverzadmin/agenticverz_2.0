# capability_id: CAP-014
# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: Memory Service - M7 Implementation
"""
Memory Service - M7 Implementation

Provides memory integration with:
- Redis caching layer with fail-open behavior
- Database persistence
- Audit logging
- Prometheus metrics
- Update rules engine integration

Usage:
    from app.memory.memory_service import MemoryService

    service = MemoryService(db_session_factory, redis_client)
    memory = await service.get("agent-123", "key")
    await service.set("agent-123", "key", {"data": "value"})
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger("nova.memory.service")

# Phase 4B: Decision Record Emission (DECISION_RECORD_CONTRACT v0.2)
from app.contracts.decisions import emit_memory_decision

# =============================================================================
# Configuration
# =============================================================================

MEMORY_CACHE_TTL = int(os.getenv("MEMORY_CACHE_TTL", "300"))  # 5 minutes
MEMORY_FAIL_OPEN = os.getenv("MEMORY_FAIL_OPEN", "true").lower() == "true"
MEMORY_AUDIT_ENABLED = os.getenv("MEMORY_AUDIT_ENABLED", "true").lower() == "true"
MEMORY_MAX_SIZE_BYTES = int(os.getenv("MEMORY_MAX_SIZE_BYTES", "1048576"))  # 1MB


# =============================================================================
# Prometheus Metrics
# =============================================================================

MEMORY_OPS = Counter("memory_service_operations_total", "Memory service operations", ["operation", "status", "cache"])

MEMORY_LATENCY = Histogram(
    "memory_service_latency_seconds",
    "Memory service operation latency",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

MEMORY_CACHE_HITS = Counter("memory_cache_hits_total", "Memory cache hits", ["tenant_id"])

MEMORY_CACHE_MISSES = Counter("memory_cache_misses_total", "Memory cache misses", ["tenant_id"])

MEMORY_SIZE_BYTES = Gauge("memory_value_size_bytes", "Size of memory values", ["tenant_id", "key"])

# M7: Drift detection and context injection metrics
MEMORY_CONTEXT_INJECTION_FAILURES = Counter(
    "memory_context_injection_failures_total", "Memory context injection failures", ["tenant_id", "reason"]
)

MEMORY_DR_LABELS = ["tenant_id", "severity"]
MEMORY_DRIFT_DETECTED = Counter("drift_detected_total", "Memory drift detection events", MEMORY_DR_LABELS)

# Import DRIFT_SCORE from drift_detector to avoid duplicate registration
# The metric "drift_score_current" is already registered there


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class MemoryEntry:
    """Memory entry with metadata."""

    tenant_id: str
    key: str
    value: Dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime
    ttl_seconds: Optional[int] = None
    expires_at: Optional[datetime] = None
    cache_hit: bool = False


@dataclass
class MemoryResult:
    """Result of memory operation."""

    success: bool
    entry: Optional[MemoryEntry] = None
    error: Optional[str] = None
    cache_hit: bool = False
    latency_ms: float = 0.0


# =============================================================================
# Memory Service
# =============================================================================


class MemoryService:
    """
    Memory service with caching and fail-open behavior.

    Features:
    - Redis caching layer
    - PostgreSQL persistence
    - Fail-open on cache/DB errors (returns empty rather than failing)
    - Audit logging
    - Prometheus metrics
    """

    def __init__(
        self, db_session_factory: Callable, redis_client: Optional[Any] = None, update_rules: Optional[Any] = None
    ):
        """
        Initialize memory service.

        Args:
            db_session_factory: Factory for creating DB sessions
            redis_client: Optional Redis client for caching
            update_rules: Optional update rules engine
        """
        self._db_factory = db_session_factory
        self._redis = redis_client
        self._update_rules = update_rules

    async def get(self, tenant_id: str, key: str, agent_id: Optional[str] = None) -> MemoryResult:
        """
        Get memory entry by key.

        Checks cache first, falls back to database.
        Fails open (returns None) on errors if MEMORY_FAIL_OPEN is true.
        """
        start_time = time.time()
        cache_hit = False

        try:
            # Try cache first
            if self._redis:
                try:
                    cache_key = self._make_cache_key(tenant_id, key)
                    cached = self._redis.get(cache_key)

                    if cached:
                        cache_hit = True
                        MEMORY_CACHE_HITS.labels(tenant_id=tenant_id).inc()
                        entry_data = json.loads(cached)
                        entry = MemoryEntry(
                            tenant_id=entry_data["tenant_id"],
                            key=entry_data["key"],
                            value=entry_data["value"],
                            source=entry_data.get("source", "cache"),
                            created_at=datetime.fromisoformat(entry_data["created_at"]),
                            updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                            ttl_seconds=entry_data.get("ttl_seconds"),
                            expires_at=datetime.fromisoformat(entry_data["expires_at"])
                            if entry_data.get("expires_at")
                            else None,
                            cache_hit=True,
                        )

                        result = MemoryResult(
                            success=True, entry=entry, cache_hit=True, latency_ms=(time.time() - start_time) * 1000
                        )

                        MEMORY_OPS.labels(operation="get", status="success", cache="hit").inc()
                        MEMORY_LATENCY.labels(operation="get").observe(time.time() - start_time)
                        self._audit("get", tenant_id, key, agent_id, cache_hit=True, success=True)

                        # Phase 4B: Emit memory decision record
                        emit_memory_decision(
                            run_id=None,  # Memory queries happen before run assignment
                            queried=True,
                            matched=True,
                            injected=True,  # Cache hit implies injection
                            sources=["cache"],
                            reason=f"Cache hit for {tenant_id}:{key}",
                            tenant_id=tenant_id,
                        )

                        return result
                    else:
                        MEMORY_CACHE_MISSES.labels(tenant_id=tenant_id).inc()

                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
                    # Continue to DB on cache error

            # Fetch from database
            session = self._db_factory()
            try:
                from sqlalchemy import text

                result = session.execute(
                    text(
                        """
                        SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                        FROM system.memory_pins
                        WHERE tenant_id = :tenant_id
                          AND key = :key
                          AND (expires_at IS NULL OR expires_at > now())
                    """
                    ),
                    {"tenant_id": tenant_id, "key": key},
                )
                row = result.fetchone()

                if not row:
                    MEMORY_OPS.labels(operation="get", status="not_found", cache="miss").inc()
                    MEMORY_LATENCY.labels(operation="get").observe(time.time() - start_time)
                    self._audit("get", tenant_id, key, agent_id, cache_hit=False, success=True)

                    # Phase 4B: Emit memory decision record - not found
                    emit_memory_decision(
                        run_id=None,
                        queried=True,
                        matched=False,
                        injected=False,
                        sources=None,
                        reason=f"No match for {tenant_id}:{key}",
                        tenant_id=tenant_id,
                    )

                    return MemoryResult(
                        success=True, entry=None, cache_hit=False, latency_ms=(time.time() - start_time) * 1000
                    )

                entry = MemoryEntry(
                    tenant_id=row.tenant_id,
                    key=row.key,
                    value=row.value if isinstance(row.value, dict) else json.loads(row.value),
                    source=row.source,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    ttl_seconds=row.ttl_seconds,
                    expires_at=row.expires_at,
                    cache_hit=False,
                )

                # Populate cache
                if self._redis:
                    try:
                        self._cache_entry(entry)
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")

                MEMORY_OPS.labels(operation="get", status="success", cache="miss").inc()
                MEMORY_LATENCY.labels(operation="get").observe(time.time() - start_time)
                self._audit("get", tenant_id, key, agent_id, cache_hit=False, success=True)

                # Phase 4B: Emit memory decision record - DB hit
                emit_memory_decision(
                    run_id=None,
                    queried=True,
                    matched=True,
                    injected=True,  # DB hit implies injection
                    sources=["database"],
                    reason=f"DB hit for {tenant_id}:{key}",
                    tenant_id=tenant_id,
                )

                return MemoryResult(
                    success=True, entry=entry, cache_hit=False, latency_ms=(time.time() - start_time) * 1000
                )

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Memory get error: {e}")
            MEMORY_OPS.labels(operation="get", status="error", cache="none").inc()
            MEMORY_LATENCY.labels(operation="get").observe(time.time() - start_time)
            self._audit("get", tenant_id, key, agent_id, cache_hit=False, success=False, error=str(e))

            if MEMORY_FAIL_OPEN:
                return MemoryResult(
                    success=True,  # Fail open
                    entry=None,
                    error=str(e),
                    cache_hit=False,
                    latency_ms=(time.time() - start_time) * 1000,
                )
            else:
                return MemoryResult(
                    success=False,
                    entry=None,
                    error=str(e),
                    cache_hit=False,
                    latency_ms=(time.time() - start_time) * 1000,
                )

    async def set(
        self,
        tenant_id: str,
        key: str,
        value: Dict[str, Any],
        source: str = "api",
        ttl_seconds: Optional[int] = None,
        agent_id: Optional[str] = None,
    ) -> MemoryResult:
        """
        Set memory entry.

        Writes to database and updates cache.
        Applies update rules if configured.
        """
        start_time = time.time()

        # Check size limit
        value_json = json.dumps(value)
        if len(value_json) > MEMORY_MAX_SIZE_BYTES:
            return MemoryResult(
                success=False,
                error=f"Value exceeds maximum size of {MEMORY_MAX_SIZE_BYTES} bytes",
                latency_ms=(time.time() - start_time) * 1000,
            )

        # Apply update rules if configured
        if self._update_rules:
            try:
                value = await self._update_rules.apply(tenant_id, key, value)
            except Exception as e:
                logger.warning(f"Update rules error: {e}")

        try:
            # Compute hash for audit
            old_hash = None
            existing = await self.get(tenant_id, key, agent_id)
            if existing.entry:
                old_hash = self._hash_value(existing.entry.value)

            new_hash = self._hash_value(value)

            # Write to database
            session = self._db_factory()
            try:
                from sqlalchemy import text

                result = session.execute(
                    text(
                        """
                        INSERT INTO system.memory_pins (tenant_id, key, value, source, ttl_seconds)
                        VALUES (:tenant_id, :key, :value::jsonb, :source, :ttl_seconds)
                        ON CONFLICT (tenant_id, key)
                        DO UPDATE SET
                            value = EXCLUDED.value,
                            source = EXCLUDED.source,
                            ttl_seconds = EXCLUDED.ttl_seconds,
                            updated_at = now()
                        RETURNING id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                    """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "key": key,
                        "value": value_json,
                        "source": source,
                        "ttl_seconds": ttl_seconds,
                    },
                )
                session.commit()

                row = result.fetchone()
                entry = MemoryEntry(
                    tenant_id=row.tenant_id,
                    key=row.key,
                    value=row.value if isinstance(row.value, dict) else json.loads(row.value),
                    source=row.source,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    ttl_seconds=row.ttl_seconds,
                    expires_at=row.expires_at,
                )

                # Update cache
                if self._redis:
                    try:
                        self._cache_entry(entry)
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")

                # Update size metric
                MEMORY_SIZE_BYTES.labels(tenant_id=tenant_id, key=key).set(len(value_json))

                MEMORY_OPS.labels(operation="set", status="success", cache="write").inc()
                MEMORY_LATENCY.labels(operation="set").observe(time.time() - start_time)
                self._audit(
                    "set", tenant_id, key, agent_id, cache_hit=False, success=True, old_hash=old_hash, new_hash=new_hash
                )

                return MemoryResult(success=True, entry=entry, latency_ms=(time.time() - start_time) * 1000)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Memory set error: {e}")
            MEMORY_OPS.labels(operation="set", status="error", cache="none").inc()
            MEMORY_LATENCY.labels(operation="set").observe(time.time() - start_time)
            self._audit("set", tenant_id, key, agent_id, cache_hit=False, success=False, error=str(e))

            return MemoryResult(success=False, error=str(e), latency_ms=(time.time() - start_time) * 1000)

    async def delete(self, tenant_id: str, key: str, agent_id: Optional[str] = None) -> MemoryResult:
        """Delete memory entry."""
        start_time = time.time()

        try:
            # Get existing for audit
            existing = await self.get(tenant_id, key, agent_id)
            old_hash = self._hash_value(existing.entry.value) if existing.entry else None

            # Delete from database
            session = self._db_factory()
            try:
                from sqlalchemy import text

                result = session.execute(
                    text(
                        """
                        DELETE FROM system.memory_pins
                        WHERE tenant_id = :tenant_id AND key = :key
                        RETURNING id
                    """
                    ),
                    {"tenant_id": tenant_id, "key": key},
                )
                session.commit()

                deleted = result.fetchone() is not None

                # Remove from cache
                if self._redis:
                    try:
                        cache_key = self._make_cache_key(tenant_id, key)
                        self._redis.delete(cache_key)
                    except Exception as e:
                        logger.warning(f"Cache delete error: {e}")

                status = "success" if deleted else "not_found"
                MEMORY_OPS.labels(operation="delete", status=status, cache="delete").inc()
                MEMORY_LATENCY.labels(operation="delete").observe(time.time() - start_time)
                self._audit("delete", tenant_id, key, agent_id, cache_hit=False, success=True, old_hash=old_hash)

                return MemoryResult(success=True, latency_ms=(time.time() - start_time) * 1000)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Memory delete error: {e}")
            MEMORY_OPS.labels(operation="delete", status="error", cache="none").inc()
            self._audit("delete", tenant_id, key, agent_id, cache_hit=False, success=False, error=str(e))

            if MEMORY_FAIL_OPEN:
                return MemoryResult(success=True, error=str(e), latency_ms=(time.time() - start_time) * 1000)
            else:
                return MemoryResult(success=False, error=str(e), latency_ms=(time.time() - start_time) * 1000)

    async def list(
        self, tenant_id: str, prefix: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[MemoryEntry]:
        """List memory entries for tenant."""
        start_time = time.time()

        try:
            session = self._db_factory()
            try:
                from sqlalchemy import text

                where_clauses = ["tenant_id = :tenant_id", "(expires_at IS NULL OR expires_at > now())"]
                params: Dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

                if prefix:
                    where_clauses.append("key LIKE :prefix")
                    params["prefix"] = f"{prefix}%"

                where_sql = " AND ".join(where_clauses)

                result = session.execute(
                    text(
                        f"""
                        SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                        FROM system.memory_pins
                        WHERE {where_sql}
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    ),
                    params,
                )

                entries = []
                for row in result:
                    entries.append(
                        MemoryEntry(
                            tenant_id=row.tenant_id,
                            key=row.key,
                            value=row.value if isinstance(row.value, dict) else json.loads(row.value),
                            source=row.source,
                            created_at=row.created_at,
                            updated_at=row.updated_at,
                            ttl_seconds=row.ttl_seconds,
                            expires_at=row.expires_at,
                        )
                    )

                MEMORY_OPS.labels(operation="list", status="success", cache="none").inc()
                MEMORY_LATENCY.labels(operation="list").observe(time.time() - start_time)

                return entries

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Memory list error: {e}")
            MEMORY_OPS.labels(operation="list", status="error", cache="none").inc()

            if MEMORY_FAIL_OPEN:
                return []
            else:
                raise

    def _make_cache_key(self, tenant_id: str, key: str) -> str:
        """Generate cache key."""
        return f"memory:{tenant_id}:{key}"

    def _cache_entry(self, entry: MemoryEntry) -> None:
        """Cache an entry in Redis."""
        if not self._redis:
            return

        cache_key = self._make_cache_key(entry.tenant_id, entry.key)
        data = {
            "tenant_id": entry.tenant_id,
            "key": entry.key,
            "value": entry.value,
            "source": entry.source,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "ttl_seconds": entry.ttl_seconds,
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
        }

        # Use entry TTL if set, otherwise default cache TTL
        ttl = entry.ttl_seconds if entry.ttl_seconds else MEMORY_CACHE_TTL
        self._redis.setex(cache_key, ttl, json.dumps(data))

    def _hash_value(self, value: Dict[str, Any]) -> str:
        """Compute hash of value for audit."""
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]

    def _audit(
        self,
        operation: str,
        tenant_id: str,
        key: str,
        agent_id: Optional[str] = None,
        cache_hit: bool = False,
        success: bool = True,
        error: Optional[str] = None,
        old_hash: Optional[str] = None,
        new_hash: Optional[str] = None,
    ) -> None:
        """Write audit log to database."""
        if not MEMORY_AUDIT_ENABLED:
            return

        try:
            session = self._db_factory()
            try:
                from sqlalchemy import text

                session.execute(
                    text(
                        """
                        INSERT INTO system.memory_audit
                        (operation, tenant_id, key, agent_id, cache_hit, success, error_message, old_value_hash, new_value_hash)
                        VALUES (:operation, :tenant_id, :key, :agent_id, :cache_hit, :success, :error, :old_hash, :new_hash)
                    """
                    ),
                    {
                        "operation": operation,
                        "tenant_id": tenant_id,
                        "key": key,
                        "agent_id": agent_id,
                        "cache_hit": cache_hit,
                        "success": success,
                        "error": error,
                        "old_hash": old_hash,
                        "new_hash": new_hash,
                    },
                )
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"Audit write error: {e}")


# =============================================================================
# Global Instance
# =============================================================================

_service: Optional[MemoryService] = None


def get_memory_service() -> Optional[MemoryService]:
    """Get global memory service instance."""
    return _service


def init_memory_service(
    db_session_factory: Callable, redis_client: Optional[Any] = None, update_rules: Optional[Any] = None
) -> MemoryService:
    """Initialize global memory service."""
    global _service
    _service = MemoryService(db_session_factory, redis_client, update_rules)
    return _service
