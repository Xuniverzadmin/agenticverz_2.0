"""
Memory Pins API - M7 Implementation

Provides REST API for managing memory pins (structured key-value storage).

Features:
- Tenant-isolated storage
- JSONB values for flexible schema
- Optional TTL for expiring entries
- RBAC enforcement (when enabled)
- Prometheus metrics

Endpoints:
- POST /api/v1/memory/pins - Create or upsert a pin
- GET /api/v1/memory/pins/{key} - Get a pin by key
- GET /api/v1/memory/pins - List pins for tenant
- DELETE /api/v1/memory/pins/{key} - Delete a pin
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from prometheus_client import Counter, Histogram
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..db import get_session as get_db_session

logger = logging.getLogger("nova.api.memory_pins")

# Feature flag
MEMORY_PINS_ENABLED = os.getenv("MEMORY_PINS_ENABLED", "true").lower() == "true"

# Prometheus metrics
MEMORY_PINS_OPERATIONS = Counter(
    "memory_pins_operations_total",
    "Total memory pin operations",
    ["operation", "status"]
)
MEMORY_PINS_LATENCY = Histogram(
    "memory_pins_latency_seconds",
    "Memory pin operation latency",
    ["operation"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class MemoryPinCreate(BaseModel):
    """Schema for creating/upserting a memory pin."""
    tenant_id: str = Field(..., min_length=1, max_length=256, description="Tenant identifier")
    key: str = Field(..., min_length=1, max_length=512, description="Pin key (unique per tenant)")
    value: Dict[str, Any] = Field(..., description="Pin value (JSON object)")
    source: str = Field(default="api", max_length=64, description="Source of the pin (api, seed, import)")
    ttl_seconds: Optional[int] = Field(default=None, ge=0, le=31536000, description="TTL in seconds (max 1 year)")

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        # Disallow certain characters for safety
        forbidden = ['..', '/', '\\', '\x00']
        for f in forbidden:
            if f in v:
                raise ValueError(f"Key cannot contain '{f}'")
        return v


class MemoryPinResponse(BaseModel):
    """Schema for memory pin response."""
    id: int
    tenant_id: str
    key: str
    value: Dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime
    ttl_seconds: Optional[int] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemoryPinListResponse(BaseModel):
    """Schema for listing memory pins."""
    pins: List[MemoryPinResponse]
    total: int
    limit: int
    offset: int


class MemoryPinDeleteResponse(BaseModel):
    """Schema for delete response."""
    deleted: bool
    key: str
    tenant_id: str


# ============================================================================
# Helper Functions
# ============================================================================

def check_feature_enabled():
    """Check if memory pins feature is enabled."""
    if not MEMORY_PINS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Memory pins feature is disabled"
        )


def extract_tenant_from_request(request: Request, tenant_id: Optional[str] = None) -> str:
    """Extract tenant ID from request or parameter."""
    # Priority: explicit param > header > default
    if tenant_id:
        return tenant_id
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant:
        return header_tenant
    return "global"


def write_memory_audit(
    db,
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
    extra: Optional[Dict[str, Any]] = None
):
    """Write an audit entry to system.memory_audit."""
    import json
    try:
        db.execute(
            text("""
                INSERT INTO system.memory_audit
                    (operation, tenant_id, key, agent_id, source, cache_hit,
                     latency_ms, success, error_message, old_value_hash, new_value_hash, extra)
                VALUES
                    (:operation, :tenant_id, :key, :agent_id, :source, :cache_hit,
                     :latency_ms, :success, :error_message, :old_value_hash, :new_value_hash, :extra)
            """),
            {
                "operation": operation,
                "tenant_id": tenant_id,
                "key": key,
                "agent_id": agent_id,
                "source": source,
                "cache_hit": cache_hit,
                "latency_ms": latency_ms,
                "success": success,
                "error_message": error_message,
                "old_value_hash": old_value_hash,
                "new_value_hash": new_value_hash,
                "extra": json.dumps(extra) if extra else "{}"
            }
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to write memory audit: {e}")
        # Don't fail the main operation if audit fails


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/pins", response_model=MemoryPinResponse, status_code=201)
async def create_or_upsert_pin(
    pin: MemoryPinCreate,
    request: Request,
    db=Depends(get_db_session)
):
    """
    Create or upsert a memory pin.

    If a pin with the same (tenant_id, key) exists, it will be updated.
    Otherwise, a new pin is created.

    Requires RBAC permission: memory_pin:write
    """
    import time
    import json
    start = time.time()
    check_feature_enabled()

    try:
        # Convert value to JSON string for PostgreSQL JSONB
        value_json = json.dumps(pin.value)

        # Use upsert (INSERT ... ON CONFLICT UPDATE)
        result = db.execute(
            text("""
                INSERT INTO system.memory_pins (tenant_id, key, value, source, ttl_seconds)
                VALUES (:tenant_id, :key, CAST(:value AS jsonb), :source, :ttl_seconds)
                ON CONFLICT (tenant_id, key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    source = EXCLUDED.source,
                    ttl_seconds = EXCLUDED.ttl_seconds,
                    updated_at = now()
                RETURNING id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
            """),
            {
                "tenant_id": pin.tenant_id,
                "key": pin.key,
                "value": value_json,
                "source": pin.source,
                "ttl_seconds": pin.ttl_seconds
            }
        )
        db.commit()

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create pin")

        response = MemoryPinResponse(
            id=row.id,
            tenant_id=row.tenant_id,
            key=row.key,
            value=row.value if isinstance(row.value, dict) else json.loads(row.value),
            source=row.source,
            created_at=row.created_at,
            updated_at=row.updated_at,
            ttl_seconds=row.ttl_seconds,
            expires_at=row.expires_at
        )

        latency_ms = (time.time() - start) * 1000
        MEMORY_PINS_OPERATIONS.labels(operation="upsert", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="upsert").observe(latency_ms / 1000)

        # Write audit log
        import hashlib
        value_hash = hashlib.sha256(value_json.encode()).hexdigest()[:16]
        write_memory_audit(
            db, operation="upsert", tenant_id=pin.tenant_id, key=pin.key,
            success=True, latency_ms=latency_ms, source=pin.source,
            new_value_hash=value_hash
        )

        logger.info(
            "memory_pin_upserted",
            extra={
                "tenant_id": pin.tenant_id,
                "key": pin.key,
                "source": pin.source,
                "has_ttl": pin.ttl_seconds is not None
            }
        )

        return response

    except IntegrityError as e:
        db.rollback()
        MEMORY_PINS_OPERATIONS.labels(operation="upsert", status="error").inc()
        logger.error(f"Integrity error creating pin: {e}")
        raise HTTPException(status_code=409, detail="Conflict creating pin")
    except Exception as e:
        db.rollback()
        MEMORY_PINS_OPERATIONS.labels(operation="upsert", status="error").inc()
        logger.error(f"Error creating pin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pins/{key}", response_model=MemoryPinResponse)
async def get_pin(
    key: str,
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    db=Depends(get_db_session)
):
    """
    Get a memory pin by key.

    Returns 404 if not found or expired.

    Requires RBAC permission: memory_pin:read
    """
    import time
    start = time.time()
    check_feature_enabled()

    try:
        result = db.execute(
            text("""
                SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                FROM system.memory_pins
                WHERE tenant_id = :tenant_id
                  AND key = :key
                  AND (expires_at IS NULL OR expires_at > now())
            """),
            {"tenant_id": tenant_id, "key": key}
        )
        row = result.fetchone()

        if not row:
            MEMORY_PINS_OPERATIONS.labels(operation="get", status="not_found").inc()
            raise HTTPException(status_code=404, detail=f"Pin not found: {key}")

        import json
        response = MemoryPinResponse(
            id=row.id,
            tenant_id=row.tenant_id,
            key=row.key,
            value=row.value if isinstance(row.value, dict) else json.loads(row.value),
            source=row.source,
            created_at=row.created_at,
            updated_at=row.updated_at,
            ttl_seconds=row.ttl_seconds,
            expires_at=row.expires_at
        )

        latency_ms = (time.time() - start) * 1000
        MEMORY_PINS_OPERATIONS.labels(operation="get", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="get").observe(latency_ms / 1000)

        # Write audit log
        write_memory_audit(
            db, operation="get", tenant_id=tenant_id, key=key,
            success=True, latency_ms=latency_ms
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        MEMORY_PINS_OPERATIONS.labels(operation="get", status="error").inc()
        logger.error(f"Error getting pin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pins", response_model=MemoryPinListResponse)
async def list_pins(
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    prefix: Optional[str] = Query(default=None, description="Key prefix filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    include_expired: bool = Query(default=False, description="Include expired pins"),
    db=Depends(get_db_session)
):
    """
    List memory pins for a tenant.

    Supports filtering by key prefix and pagination.

    Requires RBAC permission: memory_pin:read
    """
    import time
    start = time.time()
    check_feature_enabled()

    try:
        # Build query with optional filters
        where_clauses = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        if prefix:
            where_clauses.append("key LIKE :prefix")
            params["prefix"] = f"{prefix}%"

        if not include_expired:
            where_clauses.append("(expires_at IS NULL OR expires_at > now())")

        where_sql = " AND ".join(where_clauses)

        # Get total count
        count_result = db.execute(
            text(f"SELECT COUNT(*) FROM system.memory_pins WHERE {where_sql}"),
            params
        )
        total = count_result.scalar()

        # Get pins
        result = db.execute(
            text(f"""
                SELECT id, tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                FROM system.memory_pins
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        )

        import json
        pins = []
        for row in result:
            pins.append(MemoryPinResponse(
                id=row.id,
                tenant_id=row.tenant_id,
                key=row.key,
                value=row.value if isinstance(row.value, dict) else json.loads(row.value),
                source=row.source,
                created_at=row.created_at,
                updated_at=row.updated_at,
                ttl_seconds=row.ttl_seconds,
                expires_at=row.expires_at
            ))

        MEMORY_PINS_OPERATIONS.labels(operation="list", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="list").observe(time.time() - start)

        return MemoryPinListResponse(
            pins=pins,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        MEMORY_PINS_OPERATIONS.labels(operation="list", status="error").inc()
        logger.error(f"Error listing pins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pins/{key}", response_model=MemoryPinDeleteResponse)
async def delete_pin(
    key: str,
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    db=Depends(get_db_session)
):
    """
    Delete a memory pin by key.

    Returns 404 if not found.

    Requires RBAC permission: memory_pin:delete
    """
    import time
    start = time.time()
    check_feature_enabled()

    try:
        result = db.execute(
            text("""
                DELETE FROM system.memory_pins
                WHERE tenant_id = :tenant_id AND key = :key
                RETURNING id
            """),
            {"tenant_id": tenant_id, "key": key}
        )
        db.commit()

        deleted_row = result.fetchone()
        if not deleted_row:
            MEMORY_PINS_OPERATIONS.labels(operation="delete", status="not_found").inc()
            raise HTTPException(status_code=404, detail=f"Pin not found: {key}")

        latency_ms = (time.time() - start) * 1000
        MEMORY_PINS_OPERATIONS.labels(operation="delete", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="delete").observe(latency_ms / 1000)

        # Write audit log
        write_memory_audit(
            db, operation="delete", tenant_id=tenant_id, key=key,
            success=True, latency_ms=latency_ms
        )

        logger.info(
            "memory_pin_deleted",
            extra={"tenant_id": tenant_id, "key": key}
        )

        return MemoryPinDeleteResponse(
            deleted=True,
            key=key,
            tenant_id=tenant_id
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        MEMORY_PINS_OPERATIONS.labels(operation="delete", status="error").inc()
        logger.error(f"Error deleting pin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pins/cleanup", status_code=200)
async def cleanup_expired_pins(
    request: Request,
    tenant_id: Optional[str] = Query(default=None, description="Limit to specific tenant"),
    db=Depends(get_db_session)
):
    """
    Clean up expired memory pins.

    Typically called by a cron job. Deletes all pins where expires_at < now().

    Requires RBAC permission: memory_pin:admin
    """
    import time
    start = time.time()
    check_feature_enabled()

    try:
        if tenant_id:
            result = db.execute(
                text("""
                    DELETE FROM system.memory_pins
                    WHERE tenant_id = :tenant_id
                      AND expires_at IS NOT NULL
                      AND expires_at < now()
                    RETURNING id
                """),
                {"tenant_id": tenant_id}
            )
        else:
            result = db.execute(
                text("""
                    DELETE FROM system.memory_pins
                    WHERE expires_at IS NOT NULL
                      AND expires_at < now()
                    RETURNING id
                """)
            )

        db.commit()
        deleted_count = len(result.fetchall())

        MEMORY_PINS_OPERATIONS.labels(operation="cleanup", status="success").inc()
        MEMORY_PINS_LATENCY.labels(operation="cleanup").observe(time.time() - start)

        logger.info(
            "memory_pins_cleanup",
            extra={"deleted_count": deleted_count, "tenant_id": tenant_id}
        )

        return {
            "deleted_count": deleted_count,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        db.rollback()
        MEMORY_PINS_OPERATIONS.labels(operation="cleanup", status="error").inc()
        logger.error(f"Error cleaning up pins: {e}")
        raise HTTPException(status_code=500, detail=str(e))
