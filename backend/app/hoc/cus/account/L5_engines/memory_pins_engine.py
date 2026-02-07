# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: Prometheus metrics (memory_pins_operations_total, memory_pins_latency_seconds)
#   Subscribes: none
# Data Access:
#   Reads: via L6 memory_pins_driver
#   Writes: via L6 memory_pins_driver
# Role: Memory pins business logic — feature flags, validation, metrics, audit
# Callers: account_handler.py (L4)
# Allowed Imports: L5_schemas, L6_drivers
# Forbidden Imports: L2, sqlalchemy, session management
# artifact_class: CODE

"""
Memory Pins Engine (L5)

Business logic for memory pin operations.
Handles: feature flag check, validation, metrics recording, audit trail.
Delegates all DB access to L6 memory_pins_driver.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.hoc.cus.account.L6_drivers.memory_pins_driver import (
    MemoryPinRow,
)
from app.utils.metrics_helpers import get_or_create_counter, get_or_create_histogram

logger = logging.getLogger("nova.hoc.account.L5.memory_pins_engine")

MEMORY_PINS_ENABLED = os.getenv("MEMORY_PINS_ENABLED", "true").lower() == "true"

MEMORY_PINS_OPERATIONS = get_or_create_counter(
    "memory_pins_operations_total",
    "Total memory pin operations",
    ["operation", "status"],
)
MEMORY_PINS_LATENCY = get_or_create_histogram(
    "memory_pins_latency_seconds",
    "Memory pin operation latency",
    ["operation"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


class MemoryPinsDisabledError(Exception):
    """Raised when memory pins feature is disabled."""


@dataclass
class MemoryPinResult:
    """Result of a memory pin operation."""

    pin: Optional[MemoryPinRow] = None
    pins: Optional[List[MemoryPinRow]] = None
    total: int = 0
    deleted: bool = False
    deleted_count: int = 0
    key: str = ""
    tenant_id: str = ""
    limit: int = 0
    offset: int = 0
    timestamp: Optional[str] = None


class MemoryPinsDriverPort(Protocol):
    """Port for L6 driver methods used by MemoryPinsEngine."""

    async def upsert_pin(
        self,
        *,
        tenant_id: str,
        key: str,
        value: Dict[str, Any],
        source: str,
        ttl_seconds: Optional[int],
    ) -> MemoryPinRow:
        ...

    async def get_pin(
        self,
        *,
        tenant_id: str,
        key: str,
    ) -> Optional[MemoryPinRow]:
        ...

    async def list_pins(
        self,
        *,
        tenant_id: str,
        prefix: Optional[str] = None,
        include_expired: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[MemoryPinRow], int]:
        ...

    async def delete_pin(
        self,
        *,
        tenant_id: str,
        key: str,
    ) -> bool:
        ...

    async def cleanup_expired(
        self,
        *,
        tenant_id: Optional[str] = None,
    ) -> int:
        ...

    async def write_audit(
        self,
        *,
        operation: str,
        tenant_id: str,
        key: str,
        success: bool,
        latency_ms: float,
        agent_id: Optional[str] = None,
        source: Optional[str] = None,
        cache_hit: bool = False,
        error_message: Optional[str] = None,
        old_value_hash: Optional[str] = None,
        new_value_hash: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        ...


class MemoryPinsEngine:
    """Business logic for memory pin operations."""

    def _check_enabled(self) -> None:
        if not MEMORY_PINS_ENABLED:
            raise MemoryPinsDisabledError("Memory pins feature is disabled")

    async def upsert_pin(
        self,
        driver: MemoryPinsDriverPort,
        *,
        tenant_id: str,
        key: str,
        value: Dict[str, Any],
        source: str = "api",
        ttl_seconds: Optional[int] = None,
    ) -> MemoryPinResult:
        """Create or update a memory pin."""
        self._check_enabled()
        start = time.time()

        pin = await driver.upsert_pin(
            tenant_id=tenant_id,
            key=key,
            value=value,
            source=source,
            ttl_seconds=ttl_seconds,
        )

        latency_ms = (time.time() - start) * 1000
        MEMORY_PINS_OPERATIONS.labels(operation="upsert", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="upsert").observe(latency_ms / 1000)

        import json
        value_hash = hashlib.sha256(json.dumps(value).encode()).hexdigest()[:16]
        await driver.write_audit(
            operation="upsert",
            tenant_id=tenant_id,
            key=key,
            success=True,
            latency_ms=latency_ms,
            source=source,
            new_value_hash=value_hash,
        )

        logger.info(
            "memory_pin_upserted",
            extra={"tenant_id": tenant_id, "key": key, "source": source, "has_ttl": ttl_seconds is not None},
        )

        return MemoryPinResult(pin=pin)

    async def get_pin(
        self,
        driver: MemoryPinsDriverPort,
        *,
        tenant_id: str,
        key: str,
    ) -> MemoryPinResult:
        """Get a memory pin by key."""
        self._check_enabled()
        start = time.time()

        pin = await driver.get_pin(tenant_id=tenant_id, key=key)
        latency_ms = (time.time() - start) * 1000

        if pin is None:
            MEMORY_PINS_OPERATIONS.labels(operation="get", status="not_found").inc()
            return MemoryPinResult(pin=None, key=key, tenant_id=tenant_id)

        MEMORY_PINS_OPERATIONS.labels(operation="get", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="get").observe(latency_ms / 1000)

        await driver.write_audit(
            operation="get",
            tenant_id=tenant_id,
            key=key,
            success=True,
            latency_ms=latency_ms,
        )

        return MemoryPinResult(pin=pin)

    async def list_pins(
        self,
        driver: MemoryPinsDriverPort,
        *,
        tenant_id: str,
        prefix: Optional[str] = None,
        include_expired: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> MemoryPinResult:
        """List pins for a tenant."""
        self._check_enabled()
        start = time.time()

        pins, total = await driver.list_pins(
            tenant_id=tenant_id,
            prefix=prefix,
            include_expired=include_expired,
            limit=limit,
            offset=offset,
        )

        MEMORY_PINS_OPERATIONS.labels(operation="list", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="list").observe(time.time() - start)

        return MemoryPinResult(pins=pins, total=total, limit=limit, offset=offset)

    async def delete_pin(
        self,
        driver: MemoryPinsDriverPort,
        *,
        tenant_id: str,
        key: str,
    ) -> MemoryPinResult:
        """Delete a memory pin."""
        self._check_enabled()
        start = time.time()

        deleted = await driver.delete_pin(tenant_id=tenant_id, key=key)
        latency_ms = (time.time() - start) * 1000

        if not deleted:
            MEMORY_PINS_OPERATIONS.labels(operation="delete", status="not_found").inc()
            return MemoryPinResult(deleted=False, key=key, tenant_id=tenant_id)

        MEMORY_PINS_OPERATIONS.labels(operation="delete", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="delete").observe(latency_ms / 1000)

        await driver.write_audit(
            operation="delete",
            tenant_id=tenant_id,
            key=key,
            success=True,
            latency_ms=latency_ms,
        )

        logger.info("memory_pin_deleted", extra={"tenant_id": tenant_id, "key": key})

        return MemoryPinResult(deleted=True, key=key, tenant_id=tenant_id)

    async def cleanup_expired(
        self,
        driver: MemoryPinsDriverPort,
        *,
        tenant_id: Optional[str] = None,
    ) -> MemoryPinResult:
        """Clean up expired pins."""
        self._check_enabled()
        start = time.time()

        deleted_count = await driver.cleanup_expired(tenant_id=tenant_id)

        MEMORY_PINS_OPERATIONS.labels(operation="cleanup", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="cleanup").observe(time.time() - start)

        logger.info("memory_pins_cleanup", extra={"deleted_count": deleted_count, "tenant_id": tenant_id})

        return MemoryPinResult(
            deleted_count=deleted_count,
            tenant_id=tenant_id or "",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


_instance: Optional[MemoryPinsEngine] = None


def get_memory_pins_engine() -> MemoryPinsEngine:
    """Get or create the singleton MemoryPinsEngine."""
    global _instance
    if _instance is None:
        _instance = MemoryPinsEngine()
    return _instance
