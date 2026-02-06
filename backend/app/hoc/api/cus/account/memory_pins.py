# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Memory pins REST API (tenant-isolated key-value storage)
# Callers: SDK, Console UI
# Allowed Imports: L4 (operation_registry)
# Forbidden Imports: L1, L5, L6, sqlalchemy
# Reference: HOC Phase Plan — Gate 1 B2

"""
Memory Pins API - M7 Implementation

Provides REST API for managing memory pins (structured key-value storage).

Features:
- Tenant-isolated storage
- JSONB values for flexible schema
- Optional TTL for expiring entries
- RBAC enforcement (when enabled)
- Prometheus metrics (via L5 engine)

Endpoints:
- POST /api/v1/memory/pins - Create or upsert a pin
- GET /api/v1/memory/pins/{key} - Get a pin by key
- GET /api/v1/memory/pins - List pins for tenant
- DELETE /api/v1/memory/pins/{key} - Delete a pin
- POST /api/v1/memory/pins/cleanup - Clean up expired pins

All DB access routed through L4 operation registry → L5 engine → L6 driver.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.memory_pins")

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

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        forbidden = ["..", "/", "\\", "\x00"]
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


def extract_tenant_from_request(request: Request, tenant_id: Optional[str] = None) -> str:
    """Extract tenant ID from request or parameter."""
    if tenant_id:
        return tenant_id
    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant:
        return header_tenant
    return "global"


def _pin_row_to_response(pin: Any) -> MemoryPinResponse:
    """Convert a MemoryPinRow dataclass to response model."""
    return MemoryPinResponse(
        id=pin.id,
        tenant_id=pin.tenant_id,
        key=pin.key,
        value=pin.value,
        source=pin.source,
        created_at=pin.created_at,
        updated_at=pin.updated_at,
        ttl_seconds=pin.ttl_seconds,
        expires_at=pin.expires_at,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/pins", response_model=MemoryPinResponse, status_code=201)
async def create_or_upsert_pin(
    pin: MemoryPinCreate,
    request: Request,
    session = Depends(get_session_dep),
):
    """
    Create or upsert a memory pin.

    If a pin with the same (tenant_id, key) exists, it will be updated.
    Otherwise, a new pin is created.

    Requires RBAC permission: memory_pin:write
    """
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "account.memory_pins",
            OperationContext(
                session=session,
                tenant_id=pin.tenant_id,
                params={
                    "method": "upsert_pin",
                    "key": pin.key,
                    "value": pin.value,
                    "source": pin.source,
                    "ttl_seconds": pin.ttl_seconds,
                },
            ),
        )
        if not op.success:
            if op.error_code == "FEATURE_DISABLED":
                raise HTTPException(status_code=503, detail="Memory pins feature is disabled")
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

        return wrap_dict(_pin_row_to_response(op.data.pin).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MEMORY_PINS] upsert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pins/{key}", response_model=MemoryPinResponse)
async def get_pin(
    key: str,
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    session = Depends(get_session_dep),
):
    """
    Get a memory pin by key.

    Returns 404 if not found or expired.

    Requires RBAC permission: memory_pin:read
    """
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "account.memory_pins",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"method": "get_pin", "key": key},
            ),
        )
        if not op.success:
            if op.error_code == "FEATURE_DISABLED":
                raise HTTPException(status_code=503, detail="Memory pins feature is disabled")
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

        if op.data.pin is None:
            raise HTTPException(status_code=404, detail=f"Pin not found: {key}")

        return wrap_dict(_pin_row_to_response(op.data.pin).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MEMORY_PINS] get failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pins", response_model=MemoryPinListResponse)
async def list_pins(
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    prefix: Optional[str] = Query(default=None, description="Key prefix filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    include_expired: bool = Query(default=False, description="Include expired pins"),
    session = Depends(get_session_dep),
):
    """
    List memory pins for a tenant.

    Supports filtering by key prefix and pagination.

    Requires RBAC permission: memory_pin:read
    """
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "account.memory_pins",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_pins",
                    "prefix": prefix,
                    "include_expired": include_expired,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            if op.error_code == "FEATURE_DISABLED":
                raise HTTPException(status_code=503, detail="Memory pins feature is disabled")
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

        pins = [_pin_row_to_response(p) for p in (op.data.pins or [])]
        return MemoryPinListResponse(pins=pins, total=op.data.total, limit=limit, offset=offset)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MEMORY_PINS] list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pins/{key}", response_model=MemoryPinDeleteResponse)
async def delete_pin(
    key: str,
    request: Request,
    tenant_id: str = Query(default="global", description="Tenant ID"),
    session = Depends(get_session_dep),
):
    """
    Delete a memory pin by key.

    Returns 404 if not found.

    Requires RBAC permission: memory_pin:delete
    """
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "account.memory_pins",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"method": "delete_pin", "key": key},
            ),
        )
        if not op.success:
            if op.error_code == "FEATURE_DISABLED":
                raise HTTPException(status_code=503, detail="Memory pins feature is disabled")
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

        if not op.data.deleted:
            raise HTTPException(status_code=404, detail=f"Pin not found: {key}")

        return MemoryPinDeleteResponse(deleted=True, key=key, tenant_id=tenant_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MEMORY_PINS] delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pins/cleanup", status_code=200)
async def cleanup_expired_pins(
    request: Request,
    tenant_id: Optional[str] = Query(default=None, description="Limit to specific tenant"),
    session = Depends(get_session_dep),
):
    """
    Clean up expired memory pins.

    Typically called by a cron job. Deletes all pins where expires_at < now().

    Requires RBAC permission: memory_pin:admin
    """
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "account.memory_pins",
            OperationContext(
                session=session,
                tenant_id=tenant_id or "system",
                params={"method": "cleanup_expired", "tenant_id": tenant_id},
            ),
        )
        if not op.success:
            if op.error_code == "FEATURE_DISABLED":
                raise HTTPException(status_code=503, detail="Memory pins feature is disabled")
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

        return wrap_dict({
            "deleted_count": op.data.deleted_count,
            "tenant_id": tenant_id,
            "timestamp": op.data.timestamp,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MEMORY_PINS] cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
