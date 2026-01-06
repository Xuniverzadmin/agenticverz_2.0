# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: sync (request-response)
# Role: Customer activity API endpoints (L2 → L3 → L4)
# Callers: Customer Console frontend
# Allowed Imports: L3 (adapter only)
# Forbidden Imports: L4, L5, L6 (must go through L3)
# Reference: ACTIVITY Domain Qualification Task
#
# GOVERNANCE NOTE:
# This L2 file imports ONLY the L3 adapter.
# NO direct L4 service imports.
# NO direct L6 model imports.
# All business logic delegated to L3 → L4.
#
# Qualifies: ACTIVITY_LIST, ACTIVITY_DETAIL

"""
Customer Activity API (L2)

Customer-facing endpoints for viewing execution activity.
All requests are tenant-scoped and customer-safe.

Endpoints:
- GET /api/v1/customer/activity - List activities
- GET /api/v1/customer/activity/{run_id} - Get activity detail

PIN-281 Promotion:
- L4→L3: customer_activity_adapter.py (boundary adapter)
- L3→L2: This file (API route)

Rule: One adapter per route. No business logic here.
"""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query

# L3 imports ONLY (no L4, no L6!)
from app.adapters.customer_activity_adapter import (
    CustomerActivityDetail,
    CustomerActivityListResponse,
    get_customer_activity_adapter,
)

router = APIRouter(prefix="/api/v1/customer", tags=["customer-activity"])


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/activity", response_model=CustomerActivityListResponse)
def list_activities(
    limit: int = Query(default=20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    worker_id: Optional[str] = Query(default=None, description="Filter by worker"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant ID (required)"),
) -> CustomerActivityListResponse:
    """
    List activities for the current tenant.

    Returns paginated list of customer-safe activity summaries.
    All results are scoped to the authenticated tenant.

    This endpoint:
    - Shows what ran / is running
    - Provides step counts and status
    - Enables filtering by status, worker
    - Supports pagination

    No internal fields exposed (cost_cents, replay_token).

    CAPABILITY: ACTIVITY_LIST
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")

    adapter = get_customer_activity_adapter()

    try:
        return adapter.list_activities(
            tenant_id=x_tenant_id,
            limit=limit,
            offset=offset,
            status=status,
            worker_id=worker_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")


@router.get("/activity/{run_id}", response_model=CustomerActivityDetail)
def get_activity(
    run_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant ID (required)"),
) -> CustomerActivityDetail:
    """
    Get activity detail for a specific run.

    Returns customer-safe activity detail if the run exists
    and belongs to the authenticated tenant.

    This endpoint:
    - Shows detailed execution information
    - Shows recoveries and policy violations
    - Shows duration and timing
    - No cost or internal hash data

    CAPABILITY: ACTIVITY_DETAIL
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")

    adapter = get_customer_activity_adapter()

    try:
        detail = adapter.get_activity(
            tenant_id=x_tenant_id,
            run_id=run_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve activity detail")

    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Activity '{run_id}' not found or not accessible",
        )

    return detail
