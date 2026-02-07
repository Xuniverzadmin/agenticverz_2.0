# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified RATE_LIMITS facade - L2 API for rate limits and quotas
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-122 (Rate Limits API)
# GOVERNANCE NOTE:
# This is the ONE facade for RATE_LIMITS domain (usage quotas).
# All rate limit flows through this API.
# NOTE: Distinct from PIN-LIM policy limits (app/api/limits/).

"""
Rate Limits API (L2) - GAP-122

Provides rate limit and quota operations:
- GET /rate-limits (list rate limits)
- GET /rate-limits/usage (current usage)
- GET /rate-limits/{id} (get rate limit)
- PUT /rate-limits/{id} (update rate limit)
- POST /rate-limits/check (check rate limit)
- POST /rate-limits/{id}/reset (reset usage)

This is the ONLY facade for rate limit/quota operations.
Distinct from PIN-LIM policy limits (app/api/limits/).
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/rate-limits", tags=["Rate Limits"])


# =============================================================================
# Request/Response Models
# =============================================================================


class UpdateLimitRequest(BaseModel):
    """Request to update a limit."""
    max_value: Optional[int] = Field(None, description="Maximum value")
    enabled: Optional[bool] = Field(None, description="Whether limit is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CheckLimitRequest(BaseModel):
    """Request to check a limit."""
    limit_type: str = Field(..., description="Type of limit to check")
    increment: int = Field(1, description="Amount to increment if allowed")


# =============================================================================
# Endpoints (GAP-122)
# =============================================================================


@router.get("", response_model=Dict[str, Any])
async def list_limits(
    limit_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.read")),
):
    """
    List limits (GAP-122).

    Returns all configured limits for the tenant.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_limits",
                "limit_type": limit_type,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    limits = op.data

    return wrap_dict({
        "limits": [l.to_dict() for l in limits],
        "total": len(limits),
        "limit": limit,
        "offset": offset,
    })


@router.get("/usage", response_model=Dict[str, Any])
async def get_usage(
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.read")),
):
    """
    Get current usage summary.

    Returns usage across all limits with aggregated totals.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_usage"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    usage = op.data

    return wrap_dict(usage.to_dict())


@router.post("/check", response_model=Dict[str, Any])
async def check_limit(
    request: CheckLimitRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.check")),
):
    """
    Check if a limit allows an operation.

    If allowed, increments the usage counter.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "check_limit",
                "limit_type": request.limit_type,
                "increment": request.increment,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    return wrap_dict(result.to_dict())


@router.get("/{limit_id}", response_model=Dict[str, Any])
async def get_limit(
    limit_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.read")),
):
    """
    Get a specific limit.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_limit", "limit_id": limit_id},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    lim = op.data

    if not lim:
        raise HTTPException(status_code=404, detail="Limit not found")

    return wrap_dict(lim.to_dict())


@router.put("/{limit_id}", response_model=Dict[str, Any])
async def update_limit(
    limit_id: str,
    request: UpdateLimitRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.write")),
):
    """
    Update a limit configuration.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "update_limit",
                "limit_id": limit_id,
                "max_value": request.max_value,
                "enabled": request.enabled,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    lim = op.data

    if not lim:
        raise HTTPException(status_code=404, detail="Limit not found")

    return wrap_dict(lim.to_dict())


@router.post("/{limit_id}/reset", response_model=Dict[str, Any])
async def reset_limit(
    limit_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("limits.admin")),
):
    """
    Reset a limit's usage counter.

    **Requires admin permissions.**
    """
    # Get limit first to find its type
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "get_limit", "limit_id": limit_id},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    lim = op.data

    if not lim:
        raise HTTPException(status_code=404, detail="Limit not found")

    op = await registry.execute(
        "policies.rate_limits",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "reset_limit",
                "limit_type": lim.limit_type,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    return wrap_dict(result.to_dict() if result else {"success": True})
